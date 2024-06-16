
-- Query 1

CREATE VIEW RecordReturnsNew
AS
SELECT RecordReturns.title, RecordReturns.hid
FROM RecordReturns EXCEPT (
    SELECT RecordReturns.*
    FROM RecordReturns , RecordOrders
    WHERE RecordReturns.title = RecordOrders.title and
     RecordOrders.hID = RecordReturns.hID
);


CREATE VIEW RecordReturnsWithRowNumber
AS
SELECT  P.genre, P.duration,RRN.title, RRN.hID, ROW_NUMBER() over (partition by P.genre ORDER BY P.genre, P.duration DESC , RRN.title) AS row_number
FROM RecordReturnsNew RRN, Households H, Programs P
WHERE RRN.hID = H.hID and H.ChildrenNum = 0 and RRN.title = P.title
      and P.genre LIKE 'A%'
GROUP BY P.genre, P.duration, RRN.title, RRN.hID;


-- Query 2

CREATE VIEW KosherRating
As
SELECT RO.*
FROM RecordOrders RO, ProgramRanks PR, Programs P
WHERE RO.title = PR.title and RO.title = P.title and RO.hID = PR.hID and PR.rank IS NOT NULL
            UNION
SELECT RR.*
FROM RecordReturns RR, ProgramRanks PR, Programs P
WHERE RR.title = PR.title and RR.title = P.title and RR.hID = PR.hID and PR.rank IS NOT NULL;




CREATE VIEW MoreThan3
AS
SELECT KR.title
FROM KosherRating KR
GROUP BY KR.title
HAVING COUNT(KR.title) >= 3;


CREATE VIEW SolutionWithMoreThanTwoDecimals
AS
SELECT PR.title as Title, (AVG(CAST(PR.rank as decimal(10,2)))) as AverageRank
FROM ProgramRanks PR, MoreThan3 M3
WHERE PR.title = M3.title
GROUP BY PR.title;

-- Query 3


CREATE VIEW MoreThan9
As
SELECT RR.title
FROM RecordReturns RR
GROUP BY RR.title
HAVING COUNT(RR.title) >= 10;


CREATE VIEW MoreThan9WithHid
AS
SELECT MT.title, H.hID
FROM  MoreThan9 MT, Households H, RecordReturns RR
WHERE Mt.title = RR.title and RR.hID = H.hID
GROUP BY MT.title, H.hID;


CREATE VIEW NetWorth8
AS
SELECT MT.title, COUNT(MT.title) as CountNetWorth8
FROM MoreThan9WithHid MT, Households H
WHERE H.hID = MT.hID and H.netWorth >= 8
GROUP BY MT.title;


CREATE VIEW CountTitle
AS
SELECT MT.title, COUNT(MT.title) as CountTitle
FROM MoreThan9WithHid MT, Households H
WHERE H.hID = MT.hID
GROUP BY MT.title;


CREATE VIEW MoreThanHalfFamily
As
SELECT NW8.title
FROM NetWorth8 NW8, CountTitle CT
WHERE NW8.title = CT.title
      and ((CAST(NW8.CountNetWorth8 as FLOAT)) / (CAST(CT.CountTitle as FLOAT))) > 0.5;



