# 05 — Boundary case characterisation

38 cases where both the official label and the hand label fall inside
the three-node cycle. Read these to write the annotation guideline: the
question to answer for each is **what would have to be true for the other
label to be correct?**

## Directions

| Direction (official -> hand) | n |
|---|---|
| ACCURACY -> PERMISSIBLE-PURPOSE | 9 |
| INVESTIGATION -> ACCURACY | 9 |
| PERMISSIBLE-PURPOSE -> ACCURACY | 8 |
| ACCURACY -> INVESTIGATION | 7 |
| PERMISSIBLE-PURPOSE -> INVESTIGATION | 3 |
| INVESTIGATION -> PERMISSIBLE-PURPOSE | 2 |

## Signals that separate the directions

Presence rate of each lexical signal, grouped by **the label the expert
chose**. This is the operative question: if a signal is far more common in
cases labelled INVESTIGATION than in cases labelled ACCURACY, it is a
candidate rule. A low spread means the signal appears everywhere and
carries no information.

Direction-level rates are omitted deliberately: six directions across
38 cases leaves several groups at n<5, where a presence rate is forced to
0.00 or 1.00 and any spread computed from it is an artifact of the sample
size rather than a signal.

| Signal | chose_ACCURACY | chose_INVESTIGATION | chose_PERMISSIBLE-PURPOSE | spread |
|---|---|---|---|---|
| `dispute_sent` | 0.47 | 0.60 | 0.27 | **0.33** |
| `inquiry` | 0.12 | 0.20 | 0.45 | **0.33** |
| `fcra_cite` | 0.59 | 0.40 | 0.27 | **0.32** |
| `identity_theft` | 0.06 | 0.30 | 0.36 | **0.30** |
| `inaccurate` | 0.65 | 0.40 | 0.36 | **0.29** |
| `reinvestigation` | 0.47 | 0.30 | 0.18 | **0.29** |
| `permission` | 0.18 | 0.10 | 0.36 | **0.26** |
| `removal_request` | 0.29 | 0.50 | 0.36 | **0.21** |
| `verification` | 0.47 | 0.30 | 0.36 | **0.17** |
| `repeated_attempts` | 0.06 | 0.20 | 0.18 | **0.14** |
| `not_mine` | 0.12 | 0.10 | 0.00 | **0.12** |
| `no_response` | 0.00 | 0.10 | 0.09 | **0.10** |
| `thirty_days` | 0.12 | 0.10 | 0.09 | **0.03** |
| `unresolved` | 0.00 | 0.00 | 0.00 | **0.00** |

---

## ACCURACY -> INVESTIGATION  (7 cases)

### Case 2  ·  complaint 9952522

- **Official:** Incorrect information on your report
- **Hand:** Problem with a company's investigation into an existing problem
- **Your note:** Two grievances present: bureaus not responding to repeated dispute letters, and information being falsely reported. Chose the investigation issue because the non-response is what prompted the complaint. Incorrect information is defensible if you weight the stated reason for filing.

> I'm really not sure what happened. I have mailed off letters to the credit bureaus continuously and thus far I have not gotten a response. My name is XXXX XXXX and I am filing this complaint for falsely reporting misleading information. There is no third party involved. Please review the uploaded letters.

### Case 6  ·  complaint 10812654

- **Official:** Incorrect information on your report
- **Hand:** Problem with a company's investigation into an existing problem
- **Your note:** Repeated removal letters and failure to resolve the dispute are the primary grievance.

> Equifax is reporting XXXX XXXX XXXX and XXXX XXXX on my credit file. These accounts and the associated balances do not belong to me. I have sent removal letters and multiple documents many times over the course of a year. This situation is unacceptable, and they are violating several rules and regulations regarding the dispute process for accounts like these. Again, these accounts and balances do not belong to me.

### Case 10  ·  complaint 8753112

- **Official:** Incorrect information on your report
- **Hand:** Problem with a company's investigation into an existing problem

> I am writing to follow up on my previous dispute regarding the fraudulent account appearing on my credit report. On [ date of initial dispute letter ], I sent a formal dispute letter informing you of the inaccurate and unauthorized account listed on my credit report. Despite my efforts, the erroneous information has not been rectified, and I believe there may be violations of the Fair Credit Reporting Act ( FCRA ) that need to be addressed. I reiterate that I have no affiliation with this account, nor have I authorized its opening. This erroneous information is damaging my creditworthiness and causing undue stress and inconvenience. Furthermore, it has come to my attention that there may be violations of the FCRA in handling my dispute : 1. Failure to Conduct Reasonable Investigation : Despite providing sufficient evidence of the fraudulent nature of the account, no meaningful investigation appears to have been conducted to verify the accuracy of the information. 2. Failure to Provide Prompt Response : Under the FCRA, credit reporting agencies are required to investigate disputes within 30 days of receiving them. It has been well beyond this timeframe, and I have yet to receive a satisfactory response. 3. Failure to Delete Inaccurate Information : The FCRA mandates that inaccurate information must be promptly corrected or deleted from credit reports. The presence of the fraudulent account continues to mar my credit profile, indicating a failure to comply with this requirement.

### Case 47  ·  complaint 11745965

- **Official:** Incorrect information on your report
- **Hand:** Problem with a company's investigation into an existing problem
- **Your note:** Focus is repeated refusal to delete disputed accounts after proof was provided.

> Experian and XXXX refuses to delete the following accounts. XXXX XXXX XXXX charge off XXXXXXXX XXXX Its to my under that CFPB has sued these two companies for this same reason they are doing to me. I have provided proof that these accounts do not belong to me and they refuse to delete. These accounts above on my credit report. It Is hurting my financial well being and my life.

### Case 58  ·  complaint 17212981

- **Official:** Incorrect information on your report
- **Hand:** Problem with a company's investigation into an existing problem

> This complaint is valid and requires urgent action. My credit report features inaccuracies that do not uphold the highest accuracy standards. These mistakes are inflicting profound, persistent damage on my life. I require a comprehensive investigation and the immediate correction or deletion of all errors. Addressing this is imperative, not optional.

### Case 66  ·  complaint 10399080

- **Official:** Incorrect information on your report
- **Hand:** Problem with a company's investigation into an existing problem
- **Your note:** Repeated disputes with no meaningful investigation are the primary issue.

> My account with XXXX XXXX was never late! I have had exceptional payment history witH XXXX XXXX and all payments were placed on XXXX. This late payment that is reporting is a result on a systematic error on their end processing my payment. This was clearly a billing error made my the company and is not a reflection of my payment experience which violates USC Code 1681eb. This error has caused severe hard to my reputation, my character, my mode of living and to my family! I demand the late payment reported to be removed. They are not in compliance with the following law. 15 USC 1666b and its requirements set the standards and the guidance for a creditor to treat a payment as late, yet they are reporting a payment as late and they did not comply with the law! 15 USC 1666b ( a ) Time to make payments A creditor may not treat a payment on a credit card account under an open end consumer credit plan as late for any purpose, unless the creditor has adopted reasonable procedures designed to ensure that each periodic statement including the information required by section 1637 ( b ) of this title is mailed or delivered to the consumer not later than 21 days before the payment due date. XXXX XXXX never sent the periodic statement along with the disclosures from section 1637 ( b ). I have requested proof that this information was mailed or delivered 21 days before the payment due date and this information was requested in good faith pursuant rule 1002 and It was never provided. This is unfair, illegal, fraudulent, and not equitable to me as a consumer! Delete the late payments from my consumer reports

### Case 76  ·  complaint 13266601

- **Official:** Incorrect information on your report
- **Hand:** Problem with a company's investigation into an existing problem
- **Your note:** Consumer emphasizes bureaus' failure to respond to dispute letters.

> The Fair Credit Reporting Act ( 15 U.S. Code 1681 ) says ( 1 ) The banking system is dependent upon fair and accurate credit reporting. Inaccurate credit reports directly impair the efficiency of the banking system, and unfair credit reporting methods undermine the public confidence which is essential to the continued functioning of the banking system. So whenever there is a violation under the FCRA, it impairs the efficiency of the banking system. This is a violation of my privacy with my consumer report, since I control what is listed and what is not. In the event that any accounts are reported without my written consent, that is considered identity theft. This is a violation of both 15 U.S. Code 1681b ( 2 ) and 15 U.S. Code 1681c-2. This leads way to civil liability against the credit reporting agency for negligent and willful noncompliance under 15 U.S. Code 1681n, which allows for {$1000.00} per violation, for account listed without my expressed written consent.

---

## ACCURACY -> PERMISSIBLE-PURPOSE  (9 cases)

### Case 12  ·  complaint 10024363

- **Official:** Incorrect information on your report
- **Hand:** Improper use of your report
- **Your note:** Complaint is based on lack of permissible purpose/consent under FCRA §1681b.

> Please take a look at the attached letters and ID docs for verification that it is I XXXX XXXX filing this complaint. The stuff on my credit report is wrong and Under 15 U.S. Code 1681b Permissible purposes of consumer reports I never gave any written consent to report anything on my consumer reports no consent is fraud.

### Case 30  ·  complaint 9076489

- **Official:** Incorrect information on your report
- **Hand:** Improper use of your report
- **Your note:** Unauthorized inquiries are a permissible-purpose issue.

> there are a series of unauthorized Inquiries on all XXXX of the credit reporting companies. XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXXXX/XX/XXXX, I want these inquiries deleted.

### Case 40  ·  complaint 8631653

- **Official:** Incorrect information on your report
- **Hand:** Improper use of your report
- **Your note:** Disputes an unauthorized/inaccurate inquiry rather than account data.

> I am writing to formally dispute an inquiry listed on my credit report. I have carefully reviewed my credit report and have determined that this inquiry is inaccurate.

### Case 50  ·  complaint 7847537

- **Official:** Incorrect information on your report
- **Hand:** Improper use of your report
- **Your note:** Unauthorized credit inquiries.

> I just looked over a copy of my credit report. It said that the credit inquiries mentioned below were the source of the credit inquiry. But I did not authorize these investigations. As these queries are negatively impacting my ability to obtain credit and apply for loans, kindly have them erased from my credit report. Additionally, send me any supporting documents you may have for this request. XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX

### Case 52  ·  complaint 9994533

- **Official:** Incorrect information on your report
- **Hand:** Improper use of your report
- **Your note:** Complaint explicitly cites lack of permissible purpose under FCRA §1681b.

> Please take a look at the attached letters and ID docs for verification that it is I XXXX XXXX XXXX filing this complaint. The stuff on my credit report is wrong and Under 15 U.S. Code 1681b Permissible purposes of consumer reports I never gave any written consent to report anything on my consumer reports no consent is fraud.

### Case 56  ·  complaint 9482363

- **Official:** Incorrect information on your report
- **Hand:** Improper use of your report
- **Your note:** Unauthorized inquiry/permissible-purpose complaint.

> I recently reviewed a copy of my credit report and noticed I had fraudulent accounts on my report. Please remove these accounts from my report, they are hurting my ability to obtain credit.

### Case 61  ·  complaint 11525923

- **Official:** Incorrect information on your report
- **Hand:** Improper use of your report
- **Your note:** Complaint cites FCRA permissible-purpose/privacy provisions rather than data accuracy.

> I am writing to formally request the removal of an unauthorized hard inquiry from my credit report. After carefully reviewing my credit report, I noticed a hard inquiry that I did not authorize. I am concerned that this inquiry XXXX have been made in error or as a result of potential fraudulent activity. As per the Fair Credit Reporting Act ( FCRA ), I am entitled to dispute inaccurate or unauthorized information on my credit report. Since I did not initiate this credit inquiry, it should be removed from my report immediately.

### Case 75  ·  complaint 9819802

- **Official:** Incorrect information on your report
- **Hand:** Improper use of your report
- **Your note:** Complaint explicitly alleges reporting without written consent/permissible purpose under FCRA §1681b.

> I am writing to delete the following information in my file. The items I need deleted are listed in the report.I am a victim of identity theft and did not make the charge. I ask that the items be deleted to correct my credit report. I reported the theft of my identity to the Federal Trade Commission and I also have enclosed copies of the Federal Trade Commissions Identity Theft Affidavit. Please delete the items as soon as possible.

### Case 87  ·  complaint 11886886

- **Official:** Incorrect information on your report
- **Hand:** Improper use of your report
- **Your note:** Complaint focuses on FCRA privacy rights and unauthorized reporting.

> When I made the decision to use my rights under FCRA, it was with an eye on challenging any information found in credit reports that are not accurate.By fighting back against this injustice, I am ensuring that the information on my credit report is accurate and reliable.I have every right to challenge any inaccuracies in a manner compliant with federal law when they are negatively affecting me financially because of their accuracy or completeness.This is just an allegation. There's no proof that I'm delinquent or derogatory, so how can you report this? With all due respect, the claims within my report are wrong! You have to follow proper procedures if these claims are in your system and to be used in my credit reports! I challenge the accuracy and fairness of your findings by demanding evidence before you make any claims and take such drastic measures against my reputation.I know that you cant just decide which rules apply to your organization, so I won't let anyone report any false claims. it's important to make sure all of your claims are accurate and reported in the correct format- this is required by law ( FCRA ) as well as Metro 2 standards For any negative account I demand documentation / proof proving why your company considers it delinquent or derogatory. You have yet to provide me records documenting how your company verified and validated these accounts/ claims. Your proof of each negative claim you placed on my credit report should also include proof of a permissible purpose for any inquiry into the account. It's time for me to get my life back! I need you to send over some physical proof of what has been done and an updated credit report.Either confirm that this matter has been reported correctly or remove it from the report immediately. I am giving you 30 days to investigate.These allegations are without merit. Please provide accurate and verified information for each claim. If any of these claims are not true, please delete them immediately so I can restore my good name. Below is a summary of the data in which I am challenging : Summary of Accounts being challenged in list form XXXX XXXX XXXX XXXX ( XXXX ) - ( XXXX ) XXXX XXXX XXXX XXXX XXXX ( XXXX ) - ( XXXX ) XXXX XXXX XXXX ( XXXX ) - ( XXXX ) XXXX XXXX XXXX XXXX XXXX - XXXX TransUnion TransUnion Account XXXX XXXX XXXX XXXX Account XXXX XXXX Individual Account Rating : XXXX CollectionOrChargeOff Account Status : XXXX Closed Account Type : XXXX Revolving Balance Owed : XXXX {$31000.00} Close…

---

## INVESTIGATION -> ACCURACY  (9 cases)

### Case 3  ·  complaint 8476723

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Incorrect information on your report

> I am writing to formally lodge a complaint regarding inaccurate personal information on my credit report. Upon reviewing my credit report, I discovered personal information that does not belong to me, including [ XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX ]. As this erroneous information may adversely impact my creditworthiness and financial standing, I urgently request that you investigate this matter and take immediate action to rectify the inaccuracies. Your prompt attention to this issue is greatly appreciated, and I anticipate a swift resolution to ensure the accuracy and integrity of my credit report.

### Case 23  ·  complaint 9743158

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Incorrect information on your report
- **Your note:** Mortgage servicer allegedly reported late payments incorrectly.

> XXXX XXXX XXXX reported the late payment on XXXX, XXXX, XX/XX/year> to all XXXX credit bureaus for all three loans ( Loan # XXXX, XXXX and XXXX ), while those three months were the review period of mortgage assistance application.

### Case 25  ·  complaint 13934964

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Incorrect information on your report
- **Your note:** General complaint about inaccurate credit reporting.

> I am deeply disappointed by the violation of my consumer rights through the provision of inaccurate information. Fair treatment and transparency are crucial to me as a consumer. Please provide detailed information on the shortcomings regarding accuracy and compliance. Certification holds no value to me. I prioritize factual and truthful data concerning your company and my credit profile. It is concerning that the credit report I received does not adhere to the necessary standards, raising doubts about its accuracy and proper formatting. I urge you to promptly remove any false accounts from my credit report. Timely resolution is essential to prevent future financial consequences. My credit report is of utmost importance, and I expect only accurate, verified, and compliant data to be documented. Listed below is the personal information that is being challenged : Incorrect Previous Address : XXXX XXXX XXXX XXXX XXXX, XXXX, XXXX XXXX Incorrect Previous Address : XXXX XXXX XXXX XXXX XXXX XXXX, XXXX, XXXX XXXX Listed below is the account that is being challenged : XXXX XXXX XXXX below are the collections that are being challenged : XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX I respectfully contest any unverified or undocumented information in my credit report. Compliance with the FCRA and Metro 2 reporting standards is expected. Please provide factual evidence or remove any unproven claims. Mail all supporting documentation and an updated credit report. I am deeply disappointed by the inclusion of inaccurate information and the lack of supporting evidence in my credit report. It is crucial to report claims accurately and in accordance with the law. Please provide verifiable evidence to support the existence of each account and the permissible use of my information. Remove all unsupported allegations. I request that physical documentation and an updated credit report be mailed to me, as authorized. Listed below is the personal information that is being challenged : Incorrect Previous Address : XXXX XXXX XXXX XXXX XXXX XXXX, XXXX, XXXX XXXX Incorrect Name : XXXX XXXX XXXX XXXX Address : XXXX XXXX XXXX XXXX, XXXX, XXXX XXXX XXXX : Retail Listed below are the collections that are being challenged : XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX I am formally disputing any information within my credit report that lacks substantiation or accuracy, invoking both the FCRA and Metro 2 standards. The inclusion of unproven allegations of delinquency or derogatory …

### Case 59  ·  complaint 11617390

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Incorrect information on your report

> I have filed multiple disputes with XXXX, XXXX, and Experian regarding incorrect information on my credit report. Despite these efforts, the errors remain unresolved, and no sufficient action has been taken by the credit bureaus. Dispute Reasons & Violations : Failure to Verify Information ( 15 USC 1681i ( a ) ( 1 ) ) : The credit bureaus have not adequately verified the disputed information within the required 30-day period, leaving inaccurate data on my credit report. Failure to Ensure Maximum Accuracy ( 15 USC 1681e ( b ) ) : The information being reported is not the most accurate, and the bureaus have failed to take necessary steps to ensure correctness. Failure to Remove Outdated Information ( 15 USC 1681c ( a ) ( 5 ) ) : The credit bureaus have failed to remove outdated information from my report, which should have been excluded after the statutory period.

### Case 65  ·  complaint 12100375

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Incorrect information on your report

> I am filing a complaint against Equifax for failing to properly investigate my disputes regarding inaccuracies in my credit report. Despite my submissions, Equifax, Transunion & Experian consistently responds within 24 hours stating the account is accurate, without providing any evidence of a thorough investigation. This practice violates the Fair Credit Reporting Act ( FCRA ), 15 U.S.C. 1681i, which mandates a reasonable investigation of disputes. Furthermore, Equifax 's actions may also contravene the Consumer Financial Protection Act ( CFPA ), 12 U.S.C. 5536 ( a ) ( 1 ) ( A ) - ( B ), as highlighted in the CFPB 's recent administrative proceeding ( File No. XXXX ) against them for similar violations. I request that the CFPB take action to ensure Equifax complies with federal law and provides consumers with the necessary proof of investigation. XXXXXXXX XXXX XXXXXXXX

### Case 71  ·  complaint 13260479

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Incorrect information on your report

> XXXX XXXX XXXX XXXX XXXX XXXX XXXX, Florida, XXXX XX/XX/XXXX Consumer Financial Protection Bureau ( CFPB ) XXXX XXXX XXXX XXXX XXXX, IA XXXX Subject : Request for Description of Investigation Process - Disputed Accounts on My Credit Report Dear CFPB Representative, I am writing to formally dispute an inaccurate late payment entry on my credit report, as allowed under the Fair Credit Reporting Act ( 15 U.S. Code 1681i ). This inaccurate reporting has negatively affected my credit profile, and I am requesting an immediate investigation into this matter. Details of the Disputed Late Payment : Creditor Name : XXXX XXXX Account Number : # XXXXXXXX XXXX XXXX XXXX XXXX XXXX XXXX Date of Alleged Late Payment : XX/XX/XXXX I recently reviewed my credit report and noticed an account that was not reporting accurately. I had two late payments on an account that I, in fact, paid on time. The consumer reporting agencies must ensure all reported information is accurate. I have attached a copy of my report with details of the disputed dates. I request that you investigate this account and update these payments to " Paid On Time '' immediately. Legal Basis for Dispute : Fair Credit Reporting Act ( FCRA ) - 15 U.S. Code 1681i I am exercising my right under this section to dispute inaccurate information on my credit file. The reported late payment does not accurately reflect my payment history, and I am requesting a formal investigation and correction. Truth in Lending Act ( TILA ) - 15 U.S. Code 1637 ( b ) Creditors must provide clear and accurate billing statements to consumers. If this late payment reporting does not align with the terms of my agreement, it constitutes an error that should be rectified immediately. Obligations of Information Furnishers - 15 U.S. Code 1681s-2 Creditors and furnishers must ensure the accuracy of the information reported to credit bureaus. If the creditor can not substantiate the late payment with verifiable documentation, they must remove it from my credit file. Request for Description of Investigation Process : Pursuant to 15 U.S. Code 1681i ( a ) ( 7 ), credit reporting agencies must provide a description of the investigation process within 15 days of receiving a consumers dispute. Therefore, I request a detailed explanation of the procedures used to verify this account. If you can not update my payments to " Paid On Time, '' please provide the required information regarding your investigative process. Additionally, under 15 U.S.C. 1681 ( …

### Case 77  ·  complaint 8356278

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Incorrect information on your report

> I have a goal of getting a house as soon as possible but the stuff on my credit report will really put me in trouble. Ive been trying to understand some instances why the credit bureaus may take some time to respond but this is so unprofessional. My name is XXXX XXXX and I am filing this complaint for falsely reporting misleading information. Please take note, it is me personally who is filling this. There is no third party involved. Please review the uploaded letters.

### Case 78  ·  complaint 11907839

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Incorrect information on your report

> XX/XX/XXXX Subject : Fourth Round Complaint Regarding Inaccurate Late Payment Reporting on XXXXXXXX XXXX XXXXXXXX Account Dear CFPB, I am filing a formal complaint against Equifax, XXXX, and XXXX for their failure to correct inaccurate information regarding late payments reported on my credit report for the following account : Account Details : Account Name : XXXX XXXX XXXXXXXX Account Number : XXXX High Balance : {$1900.00} ( XXXX and XXXX ), {$0.00} ( Equifax ) Date Opened : XX/XX/XXXX Balance Owed : {$0.00} Closed Date : XX/XX/XXXX ( XXXX XXXX Account Status : Closed ( XXXX and XXXX ), Open ( Equifax ) Payment Status : Late XXXX XXXX ( XXXX and XXXX ), Current ( Equifax ) Credit Limit : {$1700.00} Despite multiple disputes initiated on XX/XX/XXXX, XX/XX/XXXX, and XX/XX/XXXX, the inaccuracies persist. While XXXX has removed the late payments, the Payment Status on the credit report continues to indicate " XXXX XXXXs Late, '' which is incorrect and misleading. Furthermore, XXXX and Equifax continue to report late payments for XX/XX/XXXX, XX/XX/XXXX, XX/XX/XXXX, XX/XX/XXXX, XX/XX/XXXX, XX/XX/XXXX, XX/XX/XXXX, and XX/XX/XXXX. These dates are inconsistent and unsupported by my payment records. Evidence of Errors and Discrepancies : Payment Status Inconsistencies : XXXX correctly removed late payments but still marks the account as " XXXX XXXX Late '' in the Payment Status field. XXXX and Equifax continue to report erroneous late payments. Account Status Discrepancies : XXXX and XXXX report the account as Closed, while Equifax lists it as Open. Credit Limit and High Balance : High balance differs across bureaus : {$1900.00} ( XXXX and XXXX ) versus {$0.00} ( Equifax ). Creditor Remarks : Equifaxs remarks state : " Consumer disputes - reinvestigation in progress, '' yet no corrections have been made. Violations of Federal Laws : 1. Fair Credit Reporting Act ( FCRA ) : 15 U.S. Code 1681i : Credit bureaus must ensure the accuracy of information and reinvestigate disputes thoroughly. 15 U.S. Code 1681e ( b ) : Credit reporting agencies are required to maintain maximum possible accuracy in consumer reports. 2. Truth in Lending Act ( TILA ) : 15 U.S. Code 1666b : Creditors must send periodic statements at least 21 days before payment due dates. Late payment reporting suggests non-compliance. 3. Protection Against Non-Payment of Obligations Act ( PAANL ) : Reinforces the necessity of timely and accurate disclosures to prevent unfair penalties. Desired Resolution : I…

### Case 91  ·  complaint 16375835

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Incorrect information on your report

> According to U.S.C. 1681 is the primary section of theFair Credit Reporting Act ( FCRA ), a federal law establishingCongressional findings and the statement of purposefor the subchapter concerning consumer reporting agencies.It requires these agencies to adopt fair and equitable procedures for collecting, evaluating, and using consumer information to ensure confidentiality, accuracy, and relevancy.The FCRA protects the privacy of consumer information used by credit reporting agencies for purposes like determining credit worthiness.

---

## INVESTIGATION -> PERMISSIBLE-PURPOSE  (2 cases)

### Case 27  ·  complaint 14982390

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Improper use of your report
- **Your note:** Complaint relies on unauthorized furnishing of credit information/privacy provisions rather than accuracy.

> In accordance with the Fair Credit Reporting act. The List of accounts below has violated my federally protected consumer rights to privacy and confidentiality under 15 USC 1681. 15 U.S.C 1681 section 602 A. States I have the right to privacy. 15 U.S.C 1681 Section 604 A Section 2 : It also states a consumer reporting agency can not furnish a account without my written instructions 15 U.S.C 1681c. ( a ) ( 5 ) Section States : no consumer reporting agency may make any consumer report containing any of the following items of information Any other adverse item of information, other than records of convictions of crimes which antedates the report by more than seven years. 15 U.S.C. 1681s-2 ( A ) ( 1 ) A person shall not furnish any information relating to a consumer to any consumer reporting agency if the person knows or has reasonable cause to believe that the information is inaccurate.

### Case 68  ·  complaint 12002147

- **Official:** Problem with a company's investigation into an existing problem
- **Hand:** Improper use of your report
- **Your note:** Unauthorized inquiry/privacy complaint.

> This has been gone going on for over a year, I have reached out 2 attorneys both stating the same thing I entered into a repayment status in XXXX. So it's been 11 years, but but then it disappeared in XXXX around the pandemic, which would explain why it did cuz. In all reality between my grant and the loans, it would be paid off with what I attended for which would be between XXXX to XX/XX/XXXX. When I withdrew, I never finished my freshman year. The Department of Education and XXXX XXXX keep sending a new application for me to fill out even though I've filled-out about 4 or 5 of them in over a year. I have provided cases, documentation of everything I've done. And they time friend, they're accusing me of going to school. There is only one true document and play, and that was electronically signed in XXXX. That is the only true documentation that I can see other than that. Let 's put it this way with the emergency relief program. Trump put in play before he lapped XXXX toward each student. Loan to help them out. My loans were gone with my grant, which I got a grant for over {$10000.00}, which is my school tuition as it pertains to the lawsuit. My school or the school I'm being accused of going to in a wrong year. Which there are documents attached here? Showing that they're billing incorrectly, falsifying documentation as well as I have emails, proving they falsified documentation because they stated, I reapplied to go to school. That is false They also stated they talked to me in the time frame. I supposedly went to school. That is false because little XXXX I talked to said, I told her my caseworker 's name problem is He did not tell me my caseworker 's name. She made up a name and then she never talked to me again. After I caught her in her lie, never reached back out. Never did anything. I even provided her the documentation of the fact that my identity was still never got back to me, which shows that school committed fraud. I want these loans completely discharged. I have flopped with this long enough. And they already got a demand letter and they were supposed to respond by XX/XX/XXXX, but apparently no one can read cause. They were supposed to give me their answer. By XX/XX/XXXX, when my attorney wrote them a demand letter. Now, again, for over a year, I provided ample documentation cases appointments, what I was doing a letter proving that I was on medical bed, rest from my sister, they have every documentation imaginable, but they're choosing not t…

---

## PERMISSIBLE-PURPOSE -> ACCURACY  (8 cases)

### Case 11  ·  complaint 13437471

- **Official:** Improper use of your report
- **Hand:** Incorrect information on your report
- **Your note:** Unauthorized inquiries are mentioned, but most of the complaint centers on inaccurate charged-off accounts.

> I recently looked at my credit profile and noticed a number of unauthorized inquiries and charged off accounts of on my profile. Those inquiries and charged off accounts consist of XXXX XXXX XXXX XX/XX/XXXX XXXX XXXX XXXX Payments XXXX XXXXCharge Off XXXX XXXX XXXX XXXX XXXXCharge off Transunion XXXX XXXX XX/XX/XXXX XXXX XXXX XXXX-Late Payments XXXX XXXX XXXXCharge Off XXXX XXXX- XXXXCharge Off Equifax XXXX Specialty - XXXX XXXX XXXX Etc. XX/XX/XXXX XXXX XXXX - XXXX, XXXX, XXXX. XX/XX/XXXX XXXX XXXX XXXX-Late Payments XXXX XXXXCharge Off XXXX XXXX XXXXCharge Off

### Case 17  ·  complaint 14988267

- **Official:** Improper use of your report
- **Hand:** Incorrect information on your report

> You have reported inaccurate and unauthorized accounts on my credit report, which is a violation of the Fair Credit Reporting Act ( 15 U.S. Code 1681i ) requiring a proper reinvestigation of disputed items, and 1681e ( b ), which mandates maximum possible accuracy. These false entries are damaging and unjust, especially since Ive never opened or authorized these accounts. If you fail to investigate and correct this, I may pursue legal action under the FCRA and FDCPA ( 15 U.S. Code 1692e ) for deceptive and misleading reporting.

### Case 29  ·  complaint 16709254

- **Official:** Improper use of your report
- **Hand:** Incorrect information on your report

> Background and Context This is a formal second-round dispute and complaint regarding the XXXX XXXX account ( Ref. XXXX ), which continues to be reported inaccurately despite prior disputes. The account was never authorized, verified, or validated under the Fair Debt Collection Practices Act ( FDCPA ), yet all three credit bureaus continue to list it with false, re-aged, and contradictory data. These inconsistencies clearly demonstrate violations of the Fair Credit Reporting Act ( FCRA ), FDCPA, and CFPB compliance standards regarding accuracy, verification, and consumer notification. Key Inconsistencies and Violations Re-Aged Account ( Illegal Under FCRA 623 ( a ) ( 5 ) ) Date Opened is reported as XX/XX/year>, suggesting a brand-new collection, yet the Last Activity is listed as XX/XX/year>, only eight months later. No original creditor or prior billing history is shown. This is a clear attempt to re-age a debt to extend its reporting period beyond the seven-year limit allowed by law. False and Contradictory Data Between Bureaus Equifax : Closed XXXX : Closed XXXX : Open A debt can not legally be both closed and open simultaneously. Impossible Dates and Fabricated Reporting Activity Start Date : XX/XX/year> Last Reported : XX/XX/year> The tradeline was allegedly reported before it even started, which is chronologically impossible and violates FCRA 1681e ( b ). No Validation of Debt Ownership No documentation or written notice proving that TEK Collect owns or has been assigned the alleged {$2300.00} debt has ever been provided. Reporting unverifiable debt violates FDCPA 809 ( b ) and FCRA 623 ( a ) ( 1 ) ( A ). Failure to Report Accurate Dispute Status Although this account was previously disputed ( as shown in system notes ), it is not properly marked as consumer disputes this account. This omission violates FDCPA 807 ( 8 ) and FCRA 623 ( a ) ( 3 ). Legal Violations FCRA Violations 15 U.S.C. 1681e ( b ) Failure to ensure maximum possible accuracy of reported information. 15 U.S.C. 1681i ( a ) ( 1 ) Failure to conduct a reasonable reinvestigation. 15 U.S.C. 1681i ( a ) ( 5 ) ( A ) - ( B ) Re-reporting or reinserting information without certification or notice to the consumer. 15 U.S.C. 1681s-2 ( a ) ( 1 ) ( A ) Furnishing information known to be inaccurate. 15 U.S.C. 1681s-2 ( b ) Failure to correct and update inaccurate data after being notified of a dispute. 15 U.S.C. 623 ( a ) ( 5 ) Illegal re-aging of an account to manipulate credit timelines. FDCPA Vi…

### Case 38  ·  complaint 11575913

- **Official:** Improper use of your report
- **Hand:** Incorrect information on your report
- **Your note:** Negative credit reporting allegedly violates SCRA protections.

> I am writing to formally dispute all negative remarks on my credit report due to the protections afforded under the Servicemembers Civil Relief Act ( SCRA ). As an active duty military service member, I am entitled to specific protections under this federal law. The SCRA prohibits creditors from making negative reports to credit bureaus regarding obligations that are subject to relief under this program. Specifically, creditors must accommodate the financial challenges that arise from military service and can not penalize service members by reporting delinquencies or defaults related to obligations covered under the Act. I request a full investigation into the negative items reported by [ list specific creditors, if known ] on my credit report. Please contact the creditors in question and verify whether their reporting practices comply with SCRA guidelines. If any inaccuracies or violations are found, I ask that these items be promptly removed or corrected on my credit report.

### Case 51  ·  complaint 16878951

- **Official:** Improper use of your report
- **Hand:** Incorrect information on your report

> The creditor or furnisher is reporting a negative account with inaccurate or incomplete information. I have reviewed my credit report and found errors in the balance, payment history, and/or account status. Under the Fair Credit Reporting Act ( FCRA ) Section 623, furnishers must report accurate and verifiable information. I have requested verification and supporting documentation from the creditor, but they failed to provide proof of accuracy. Please investigate this matter and ensure the information is corrected or deleted if unverified. XXXXXXXX XXXX XXXX ( Original Creditor : XXXX XXXX XXXX ) # XXXX XX/XX/year> -- {$440.00} XXXX XXXX ( Original Creditor : XXXX XXXX XXXX ) # XXXX XX/XX/year> -- {$980.00}

### Case 60  ·  complaint 8235710

- **Official:** Improper use of your report
- **Hand:** Incorrect information on your report

> Violations of Fair Credit Reporting Act and Privacy Laws I am making this complaint to the CFPB because you are the government entity that is supposed to make these institutions follow the law. well they are not following the law by any means. I ask that you do the job that you were created to do and protect us consumers from these Institutions. and make them answer for their indiscretions. I, XXXX XXXX, the undersigned, am writing to bring to your attention the egregious violations of my rights as a consumer by the consumer reporting agencies XXXX, XXXX and Transunion, hereinafter referred to as the " Agencies, '' and XXXX, XXXX, XXXX, XXXX, XXXX, XXXX hereinafter referred to as the " Financial Institutions. '' The violations pertain to the Fair Credit Reporting Act ( FCRA ), 15 USC 1681, and related privacy laws. I. FCRA Section 602 ( a ) - Responsibilities of Consumer Reporting Agencies According to 15 USC 1681 section 602 ( a ), it is mandated that consumer reporting agencies exercise their responsibilities with fairness, impartiality, and respect for the consumer 's right to privacy. The Agencies, have failed to adhere to these obligations. II. FCRA Section 6801 - Privacy Policy of Financial Institutions Pursuant to 15 USC 6801, it is the policy of Congress that each financial institution has an affirmative and continuing obligation to respect the privacy of its customers. The Financial Institutions, as furnishers of information to credit agencies, falls under this definition. The failure to protect the security and confidentiality of my nonpublic personal information is a clear violation. III. FCRA Section 604 ( a ) ( 2 ) - Furnishing Consumer Reports Only with Consumer Consent Under 15 USC 1681 section 604 ( a ) ( 2 ), any consumer reporting agency may furnish a consumer report only in accordance with the written instructions of the consumer to whom it relates. The Financial Institutions and the Consumer Reporting Agencies lack my explicit written consent to furnish my information. IV. FCRA Section 6802 ( b ) ( c ) - Nondisclosure Option According to 15 USC 6802 ( b ) ( c ), a financial institution may not disclose nonpublic personal information to a nonaffiliated third party unless the consumer is informed of their right to exercise the nondisclosure option. The Financial Institutions failed to provide such information, violating my rights. V. FCRA Section 1681C ( a ) ( 5 ) - Limitations on Information in Consumer Reports Pursuant to 15 USC 1681C (…

### Case 69  ·  complaint 9757032

- **Official:** Improper use of your report
- **Hand:** Incorrect information on your report

> These can be combined On my credit report, you have shown incorrect accounts that should not be there at all. This is not only unjust to me, but it's also concerning, because I've never done or made any of the things you accuse me of. If you don't look into these accounts, I'll take legal action against you.

### Case 74  ·  complaint 9167946

- **Official:** Improper use of your report
- **Hand:** Incorrect information on your report
- **Your note:** Identity theft is mentioned, but the requested remedy is deletion of fraudulent tradelines.

> I've recently received a copy of my credit reports and noticed several inaccuracies and late payments on my reports. This negative remark has been detrimental to my life and overall credit health.

---

## PERMISSIBLE-PURPOSE -> INVESTIGATION  (3 cases)

### Case 8  ·  complaint 15738333

- **Official:** Improper use of your report
- **Hand:** Problem with a company's investigation into an existing problem

> I have submitted multiple formal dispute letters to TRANSUNION LLC Consumer Dispute Center regarding inaccurate and unverifiable information on my credit report ( see attached copies ). Despite clear legal notice, TRANSUNION LLC Consumer Dispute Center continues to willfully report inaccurate data in violation of FCRA 15 U.S.C. 1681e ( b ), 1681i, and FDCPA 1692e and 1692f. I have exhausted all attempts to resolve this matter directly with the credit bureau. I now request the CFPB to investigate and enforce compliance.

### Case 54  ·  complaint 8683869

- **Official:** Improper use of your report
- **Hand:** Problem with a company's investigation into an existing problem
- **Your note:** Main complaint is failure to properly investigate/respond to disputes.

> multiple unrecognized and/or duplicated inquires to my credit file

### Case 63  ·  complaint 12244051

- **Official:** Improper use of your report
- **Hand:** Problem with a company's investigation into an existing problem

> I AM TRYING TO DISPUTE HARD INQUIRIES THAT I DON'T RECOGNIZE.

---
