from django.shortcuts import render
from django.db import connection
from . import models


# Create your views here.

flag1 = False
flag2 = False
flag3 = False


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def index(request):
    return render(request, 'index.html')


def QueryResults(request):
    with connection.cursor() as cursor:
        # Query1
        cursor.execute(
            """
            SELECT RRW.genre as Genre,RRW.title as Title,RRW.duration as Duration
            FROM RecordReturnsWithRowNumber RRW
            WHERE row_number = 1;
            """
        )
        sql_res1 = dictfetchall(cursor)

        # Query2

        cursor.execute(
            """
            SELECT S.Title, CAST(S.AverageRank as decimal(10,2)) as AverageRank
            FROM SolutionWithMoreThanTwoDecimals S
            ORDER BY S.AverageRank desc;
            """
        )
        sql_res2 = dictfetchall(cursor)

        # Query3

        cursor.execute(
            """
            SELECT MF.*
            FROM MoreThanHalfFamily MF
            WHERE MF.title NOT IN (SELECT DISTINCT PR2.title
                           FROM ProgramRanks PR2)
            OR MF.title IN (SELECT DISTINCT PR.title
                          FROM ProgramRanks PR, MoreThanHalfFamily MT1
                          WHERE MT1.title = PR.title
                          EXCEPT
                         (SELECT DISTINCT PR1.title
                          FROM ProgramRanks PR1, MoreThanHalfFamily MT2
                          WHERE PR1.rank <= 1 and MT2.title = PR1.title
                         ));
    
    
            """
        )
        sql_res3 = dictfetchall(cursor)

    return render(request, 'QueryResults.html', {'sql_res1': sql_res1, 'sql_res2': sql_res2, 'sql_res3': sql_res3})


def RecordsManagement(request):
    if not request.POST:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT Top 3 hID, COUNT(title) AS count1
                    FROM
                    (
                        SELECT hID, title FROM RecordOrders
                        UNION
                             SELECT hID, title FROM RecordReturns
                    ) AllRecords
                    GROUP BY hID
                    ORDER BY count1 DESC
                """
            )
            table = dictfetchall(cursor)
        return render(request, 'RecordsManagement.html', {"table": table})

    else:
        with connection.cursor() as cursor:
            if request.POST and request.POST.get('hIDOrder') \
                    and request.POST.get('titleOrder'):
                titleOrder = request.POST.get('titleOrder')
                hIDOrder = request.POST.get('hIDOrder')

                cursor.execute(
                    f"""
                        SELECT Top 3 hID, COUNT(*) AS count1
                        FROM
                        (
                            SELECT hID, title FROM RecordOrders
                            UNION
                            SELECT hID, title FROM RecordReturns
                        ) AllRecords
                        GROUP BY hID
                        ORDER BY count1 DESC
                    """
                )
                table = dictfetchall(cursor)

                cursor.execute(
                    f"""
                        SELECT H.hID
                        FROM Households H
                        WHERE H.hID = {hIDOrder}
                    """
                )
                hID_Order = dictfetchall(cursor)

                cursor.execute(
                    f"""
                        SELECT P.title
                        FROM Programs P
                        WHERE P.title = '{titleOrder}'
                            """
                )
                title_Order = dictfetchall(cursor)

                cursor.execute(
                    f"""
                        SELECT COUNT(RO.title) AS numberOfOrders
                        FROM RecordOrders RO
                        WHERE RO.hID = {hIDOrder}
                        GROUP BY RO.hID
                    """
                )

                numberOfOrders = dictfetchall(cursor)

                cursor.execute(
                    f"""
                        SELECT RO.hID
                        FROM RecordOrders RO
                        WHERE RO.title = '{titleOrder}'
                        """
                )

                h_id_owns_record = dictfetchall(cursor)

                cursor.execute(
                    f"""
                            SELECT RR.hID
                            FROM RecordReturns RR
                            WHERE RR.title = '{titleOrder}' and RR.hID = {hIDOrder}
                            """
                )
                h_id_returns_record = dictfetchall(cursor)

                cursor.execute(
                    f"""
                    SELECT H.ChildrenNum, P.genre
                    FROM Households H, Programs P
                    WHERE H.hID = {hIDOrder} AND P.title = '{titleOrder}'
                    """
                )
                NumAndGenreOfChildren = dictfetchall(cursor)
                if NumAndGenreOfChildren:
                    childrenNum = NumAndGenreOfChildren[0]['ChildrenNum']
                    titleGenre = NumAndGenreOfChildren[0]['genre']

                if not hID_Order:

                    return render(request, 'RecordsManagement.html',
                                  {'error': 'Family hID was not found',
                                   'table': table})

                if not title_Order:
                    return render(request, 'RecordsManagement.html',
                                  {'error': 'Movie title was not found',
                                   'table': table})

                if numberOfOrders and numberOfOrders[0]['numberOfOrders'] >= 3:
                    return render(request, 'RecordsManagement.html',
                                  {'error': 'Family has already 3 records',
                                   'table': table})

                if h_id_owns_record:
                    if str(h_id_owns_record[0]['hID']) == hIDOrder:
                        return render(request, 'RecordsManagement.html',
                                      {'error': "Family already owns this record",
                                       'table': table})
                    else:
                        return render(request, 'RecordsManagement.html',
                                      {'error': "Another family already owns this record",
                                       'table': table})

                if h_id_returns_record:
                    return render(request, 'RecordsManagement.html',
                                  {'error': "Family already ordered this record before",
                                   'table': table})

                if NumAndGenreOfChildren and childrenNum > 0 and (
                        titleGenre == 'Reality' or titleGenre == 'Adults only'):
                    return render(request, 'RecordsManagement.html',
                                  {'error': "The family has kids and the genre is inappropriate",
                                   'table': table})

                cursor.execute(
                    f"""
                        INSERT INTO RecordOrders (hID, title) VALUES ({hIDOrder}, '{titleOrder}');
                    """
                )

                cursor.execute(
                    f"""
                         SELECT Top 3 hID, COUNT(title) AS count1
                         FROM
                         (
                             SELECT hID, title FROM RecordOrders
                             UNION
                             SELECT hID, title FROM RecordReturns
                         ) AllRecords
                         GROUP BY hID
                         ORDER BY count1 DESC
                     """
                )
                table = dictfetchall(cursor)

                return render(request, 'RecordsManagement.html',
                              {'success': 'Order successfully added!',
                               'table': table})

            if request.POST and request.POST.get('hIDReturn') \
                    and request.POST.get('titleReturn'):
                titleReturn = request.POST.get('titleReturn')
                hIDReturn = request.POST.get('hIDReturn')

                cursor.execute(
                    f"""
                         SELECT Top 3 hID, COUNT(*) AS count1
                         FROM
                         (
                             SELECT hID, title FROM RecordOrders
                             UNION
                             SELECT hID, title FROM RecordReturns

                         ) AllRecords
                         GROUP BY hID
                         ORDER BY count1 DESC
                     """
                )
                table = dictfetchall(cursor)

                cursor.execute(
                    f"""
                                        SELECT H.hID
                                        FROM Households H
                                        WHERE H.hID = {hIDReturn}
                                    """
                )
                hIDReturn = dictfetchall(cursor)

                cursor.execute(
                    f"""
                                            SELECT P.title
                                        FROM Programs P
                                        WHERE P.title = '{titleReturn}'
                                            """
                )
                title_Return = dictfetchall(cursor)

                cursor.execute(
                    f"""
                                        SELECT RO1.hID
                                        FROM RecordOrders AS RO1
                                        WHERE RO1.title = '{titleReturn}'
                                        """
                )
                hIDOwnsRecordReturn = dictfetchall(cursor)

                if not hIDReturn:
                    return render(request, 'RecordsManagement.html',
                                  {'error_return': '!!Family hID was not found!!', 'table': table})

                if not title_Return:
                    return render(request, 'RecordsManagement.html',
                                  {'error_return': '!!Movie title was not found!!', 'table': table})

                if hIDOwnsRecordReturn != hIDReturn:
                    return render(request, 'RecordsManagement.html',
                                  {'error_return': '!!You can not return a movie that belongs to another family!!',
                                   'table': table})

                cursor.execute(
                    f"""
                    DELETE FROM RecordOrders WHERE hID = {hIDReturn} and title = '{titleReturn}';
                    """
                )

                cursor.execute(
                    f"""
                        INSERT INTO RecordReturns (hID, title) VALUES ({hIDReturn}, '{titleReturn}');
                    """
                )

                cursor.execute(
                    f"""
                                 SELECT Top 3 hID, COUNT(title) AS count1
                                 FROM
                                 (
                                     SELECT hID, title FROM RecordOrders
                                     UNION
                                     SELECT hID, title FROM RecordReturns
                                 ) AllRecords
                                 GROUP BY hID
                                 ORDER BY count1 DESC
                             """
                )
                table = dictfetchall(cursor)

                return render(request, 'RecordsManagement.html',
                              {'success_return': 'Order successfully returned!', 'table': table})


def Rankings(request):
    if not request.POST:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT genre
                FROM Programs AS P
                GROUP BY genre
                HAVING COUNT(P.title) >= 5
                """
            )
            allGenre = dictfetchall(cursor)
            flag = True
            cursor.execute(
                """
                    SELECT H.hID
                    FROM Households AS H
                """
            )
            allhID = dictfetchall(cursor)

            cursor.execute(
                """
                    SELECT P.title
                    FROM Programs AS P
                """
            )
            allprograms = dictfetchall(cursor)
            return render(request, 'Rankings.html',
                          {'allGenre': allGenre, 'flag': flag, 'allhID': allhID, 'allprograms': allprograms})

    else:
        with connection.cursor() as cursor:
            if request.POST and request.POST.get('hidChosen') \
                    and request.POST.get('ProgramNameChosen') \
                    and request.POST.get('rank'):
                ProgramNameChosen = request.POST.get('ProgramNameChosen')
                hidChosen = request.POST.get('hidChosen')
                rank = request.POST.get('rank')

                cursor.execute(
                    f"""
                        SELECT PR.rank
                        FROM ProgramRanks AS PR
                        WHERE PR.hID = {hidChosen} and PR.title = '{ProgramNameChosen}'
                    """
                )
                hID_Order = dictfetchall(cursor)

                if not hID_Order:
                    cursor.execute(
                        f"""
                            INSERT INTO ProgramRanks (title, hID, rank) VALUES ('{ProgramNameChosen}', {hidChosen}, {rank});
                        """
                    )
                else:
                    cursor.execute(
                        f"""
                        UPDATE ProgramRanks
                        SET rank = {rank}
                        WHERE hID = {hidChosen} AND title = '{ProgramNameChosen}';
                        """
                    )
                flag = True
                cursor.execute(
                    """
                        SELECT H.hID
                        FROM Households AS H
                    """
                )
                allhID = dictfetchall(cursor)

                cursor.execute(
                    """
                        SELECT P.title
                        FROM Programs AS P
                    """
                )
                allprograms = dictfetchall(cursor)

                cursor.execute(
                    f"""
                    SELECT genre
                    FROM Programs AS P
                    GROUP BY genre
                    HAVING COUNT(P.title) >= 5
                    """
                )
                allGenre = dictfetchall(cursor)
                return render(request, 'Rankings.html',
                              {'flag': flag, 'allhID': allhID, 'allprograms': allprograms, 'allGenre': allGenre})

            if request.POST and request.POST.get('genreChosen') and request.POST.get('minRank'):
                genreChosen = request.POST.get('genreChosen')
                minRank = request.POST.get('minRank')

                cursor.execute(
                    f"""
                    
                    SELECT TOP 5 P2.title, COALESCE(
                        (
                            SELECT CAST(AVG(CAST(rank AS FLOAT)) AS DECIMAL(10, 2)) 
                            FROM ProgramRanks PR1
                            WHERE PR1.title = P2.title
                            GROUP BY PR1.title
                            HAVING COUNT(*) >= {minRank}
                        ), 0
                    ) AS average
                    FROM Programs P2
                    WHERE P2.genre = '{genreChosen}'
                    ORDER BY average DESC, P2.title

                    """
                )
                show_spoken = dictfetchall(cursor)

                cursor.execute(
                    f"""
                                            SELECT genre
                                            FROM Programs P
                                            GROUP BY genre
                                            HAVING COUNT(P.title) >= 5
                                            """
                )
                allGenre = dictfetchall(cursor)

                cursor.execute(
                    """
                        SELECT H.hID
                        FROM Households H
                    """
                )
                allhID = dictfetchall(cursor)

                cursor.execute(
                    """
                        SELECT P.title
                        FROM Programs P
                    """
                )
                allprograms = dictfetchall(cursor)
                flag = False
                return render(request, 'Rankings.html',
                              {'show_spoken': show_spoken, 'allGenre': allGenre, 'flag': flag, 'allhID': allhID,
                               'allprograms': allprograms})
