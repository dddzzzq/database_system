CREATE TABLE AProblem (
	NUM INT NOT NULL,
    ProblemID VARCHAR(10) NOT NULL,
    ProblemName VARCHAR(100) NOT NULL,
    Company VARCHAR(50) NOT NULL,
    CONSTRAINT PK_AProblem PRIMARY KEY (NUM)
);
INSERT INTO AProblem (NUM, ProblemID, ProblemName, Company) VALUES (1, '��A01�� ', '��ó��ҵ̼����SAASϵͳ����', '������Ͱ͡�');
SELECT *
FROM APROBLEM;