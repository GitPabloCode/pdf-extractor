
---
<!-- pagina 1 -->

[¶0]
| ERTMS/ETCS                                               | ERTMS/ETCS                                               |
|----------------------------------------------------------|----------------------------------------------------------|
| System Requirements Specification Chapter 1 Introduction | System Requirements Specification Chapter 1 Introduction |
| REF :                                                    | SUBSET-026-1                                             |
| ISSUE :                                                  | 3.6.0                                                    |
| DATE :                                                   | 13/05/2016                                               |


---
<!-- pagina 2 -->

# ERA * UNISIG * EEIG ERTMS USERS GROUP [¶1]

# 1.1 Modification History [¶2]

[¶3]
| Issue Number Date     | Section Number                        | Modification / Description                                                                | Author / Editor    |
|-----------------------|---------------------------------------|-------------------------------------------------------------------------------------------|--------------------|
| 0.0.1                 | All                                   | first issue                                                                               | SAB                |
| 0.1.0                 | All                                   | Review comments from Adtranz                                                              | SAB                |
| 1.0.0                 | All                                   | Final review                                                                              | SAB                |
| 1.0.2 / 15. Apr. 1999 | All                                   | Reworked edition                                                                          | SAB                |
| 1.0.3 / 22. Apr. 1999 | 1.8.9                                 | Comment of Alstom                                                                         | SAB                |
| 1.1.0 / 23. Apr. 1999 |                                       | Final issue of class P SRS                                                                | Ch. Frerichs (ed.) |
| 1.1.1 / 27. Mai 1999  | 1.3.1.1/1.7.1.2                       | Review comments added                                                                     | SAB                |
| 1.1.2                 |                                       | Draft for class 1                                                                         | SAB                |
| 1.1.3 990729          | Document reference number.            | Revision during finalisation meeting, Stuttgart 990729                                    | HE                 |
| 1.2.0 990730          | Version number                        | Release version                                                                           | HE                 |
| 1.2.1 991209          | All                                   | First draft for 2 nd release                                                              | SAB                |
| 1.3.0 991216          | All                                   | Review comments added                                                                     | SAB                |
| 2.0.0 991222          | Minor editing                         | Finalisation                                                                              | SAB                |
| 2.0.1                 | All                                   | Corrections after review                                                                  | SAB                |
| 2.1.0                 | Version number                        | UNISIG release                                                                            | SAB                |
| 2.2.0                 | Version number                        | UNISIG release                                                                            | SAB                |
| 2.2.2 1.2.2002        | Version number                        | Final edition                                                                             | Ch. Frerichs       |
| 2.3.0 24/02/06        | Version number, no change since 2.2.2 | Release version                                                                           | HK                 |
| 3.0.0 23/12/08        | 1.8.7                                 | Release version Re-use of chapter 6, now dedicated to management of older system versions | AH                 |


---
<!-- pagina 3 -->

# ERA * UNISIG * EEIG ERTMS USERS GROUP [¶4]

[¶5]
| 3.0.1 22/12/09   |                                                                  | Including the results of the editorial review of the SRS 3.0.0                  | AH   |
|------------------|------------------------------------------------------------------|---------------------------------------------------------------------------------|------|
| 3.1.0 22/02/10   | No change                                                        | Release version                                                                 | AH   |
| 3.2.0 22/12/10   | No change                                                        | Release version                                                                 | AH   |
| 3.2.1 13/12/11   |                                                                  | Including all CR's that are in state 'Analysis completed' according to ERA CCM. | AH   |
| 3.3.0 07/03/12   |                                                                  | Baseline 3 release version                                                      | AH   |
| 3.3.1 04/04/14   | No change                                                        |                                                                                 | OG   |
| 3.3.2 23/04/14   | No change                                                        | Baseline 3 1 st maintenance pre-release version                                 | OG   |
| 3.3.3 06/05/14   | No change                                                        | Baseline 3 1 st maintenance 2 nd pre-release version                            | OG   |
| 3.4.0 12/05/14   | No change                                                        | Baseline 3 1 st maintenance release version                                     | OG   |
| 3.4.1 23/06/15   | No change                                                        |                                                                                 | OG   |
| 3.4.2 17/11/15   | CR1266                                                           |                                                                                 | OG   |
| 3.4.3 16/12/15   | Update due to overall CR consolation                             | phase                                                                           | OG   |
| 3.5.0 18/12/15   | Baseline 3 2 nd release version as EC (see ERA-REC-123-2015/REC) | recommended to                                                                  | OG   |
| 3.5.1 28/04/16   | No change                                                        |                                                                                 | OG   |
| 3.6.0 13/05/16   | Baseline 3 2 nd release                                          | version                                                                         | AH   |


---
<!-- pagina 4 -->

# 1.2 Table of Contents [¶6]

| 1.1                                                                                                                            | Modification History...........................................................................................................2     |
|--------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| 1.2                                                                                                                            | Table of Contents..............................................................................................................4     |
| 1.3                                                                                                                            | Introduction.......................................................................................................................5 |
| 1.4                                                                                                                            | Advantages of an International Interoperable System.......................................................5                          |
| 1.5                                                                                                                            | About this Document.........................................................................................................5        |
| 1.6                                                                                                                            | How to Read and Use the SRS.........................................................................................6                |
| 1.7                                                                                                                            | Requirements ...................................................................................................................6    |
| 1.8                                                                                                                            | Contents of the SRS.........................................................................................................6        |
| 1.8.2 Chapter 1: Introduction ..............................................................................................7  | 1.8.2 Chapter 1: Introduction ..............................................................................................7        |
| 1.8.3 Chapter 2: Basic System Description.........................................................................7            | 1.8.3 Chapter 2: Basic System Description.........................................................................7                  |
| 1.8.4 Chapter 3: Principles..................................................................................................7 | 1.8.4 Chapter 3: Principles..................................................................................................7       |
| 1.8.5                                                                                                                          | Chapter 4: Modes and Transitions .............................................................................7                      |
| 1.8.6                                                                                                                          | Chapter 5: Procedures...............................................................................................7                |
| 1.8.7                                                                                                                          | Chapter 6: Management of older System Versions....................................................7                                  |
| 1.8.8                                                                                                                          | Chapter 7: ERTMS/ETCS Language .........................................................................7                            |
| 1.8.9                                                                                                                          | Chapter 8: Messages.................................................................................................8                |
| 1.8.10                                                                                                                         | Chapter 9: Classification of the SRS clauses.............................................................8                           | [¶7]


---
<!-- pagina 5 -->

# 1.3 Introduction [¶8]

- 1.3.1.1 Train control is an important part of any railway operations management system. In the past  a  number  of  different  Automatic  Train  Control  (ATC)  systems  have  evolved  in different  countries  at  different  times.  These  systems  are  incompatible  and  not interoperable with each other. Only a few of these systems are used in more than one country, and even in those cases there have been differences in detailed development which have resulted in incompatible and not interoperable versions. [¶9]

- 1.3.1.2 Many  railways  anticipate  a  significant  increase  in  density  of  train  traffic  and  are rethinking their infrastructure strategy, to accommodate high levels of traffic, in which ATC  systems  play  an  important  part.  Also  many  railways  would  like  to  introduce standardised  systems  to  reduce  system  costs.  In  order  to  establish  international standardisation of ATC systems, the following document specifies the European Rail Traffic Management System/European Train Control System (ERTMS/ETCS). [¶10]

# 1.4 Advantages of an International Interoperable System [¶11]

- 1.4.1.1 The advantages expected by the railways can be summarised as: [¶12]

-  Cross border interoperability. [¶13]

-  Improvement of the safety of national and international train traffic. [¶14]

-  Improvement of international passengers and freight train traffic management. [¶15]

-  Shorter  headway  on heavily trafficked  lines,  by  driving  on  moving  block,  enabling exploitation of maximum track capacity. [¶16]

-  The possibility of step-by-step introduction of the new technology. [¶17]

-  Enabling  Pan-European competition between the manufacturers of ERTMS/ETCS components.  Strengthening  the  position  of  the  European  railway  industry  on  the world market. [¶18]

-  Enabling  preconditions  for future harmonisation  in  other  areas  of  rail traffic management. [¶19]

# 1.5 About this Document [¶20]

- 1.5.1.1 The purpose of this document is to specify the unified European Train Control System (ETCS) from a technical point of view. [¶21]

- 1.5.1.2 Some parts of the system are only specified to allow a migration from existing train control systems to ETCS (e.g. STM's) over a transition period. They might be removed in a future edition of the standard. [¶22]

- 1.5.1.3 To reach technical interoperability it is necessary not only that telegrams are generated and  understood  according  to  well  specified  rules  but  also  that  a  train  respectively [¶23]


---
<!-- pagina 6 -->

trackside  equipment  reacts  in  a  uniform  way  to  information  received.  Technical interoperability requires specifications of a detailed level. [¶24]

- 1.5.1.4 For  operational  interoperability  it  is  necessary  to  add  operating  rules,  engineering standards etc.  to  the  system  design.  Reaching  operational  interoperability  is  outside the scope of the SRS. [¶25]

# 1.6 How to Read and Use the SRS [¶26]

- 1.6.1.1 The SRS covers 9 chapters, which are briefly described in the section following this introduction. [¶27]

- 1.6.1.2 All  readers may need to refer to the Glossary of terms and abbreviations (SUBSET023). [¶28]

# 1.7 Requirements [¶29]

- 1.7.1.1 This specification defines the functions that allow reaching the technical interoperability.  This  is  materialised  through  numbered  clauses  which  are  formally identified  as  containing  ERTMS/ETCS  on-board  and/or  ERTMS/ETCS  trackside requirements (see details in chapter 9). [¶30]

- 1.7.1.2 The ERTMS/ETCS on-board equipment shall implement all its allocated requirements, with the only exceptions and conditions explicitly stated in the Control-Command and Signalling TSI and in this SRS. [¶31]

- 1.7.1.3 For  ERTMS/ETCS  trackside  the  implementation  of  functions  has  to  be  defined according to the characteristics of the specific lines and the related operational needs. In  any  case,  the  requirements  of  this  SRS,  which are  allocated  to the  trackside  and related to the implemented functions, shall be respected. [¶32]

- 1.7.1.4 Intentionally deleted. [¶33]

- 1.7.1.5 Not specified requirements and solutions shall only be permitted as long as they do not generate any interoperability problems. [¶34]

# 1.8 Contents of the SRS [¶35]

- 1.8.1.1 The  SRS  defines  the  system  requirements  for  the  European  Train  Control  System (ETCS) of ERTMS. [¶36]

- 1.8.1.2 This sub-section is intended to give a rough overview of the contents of each chapter within the SRS so that readers interested only in specialised subjects can easily find the relevant chapters. [¶37]


---
<!-- pagina 7 -->

# ERA * UNISIG * EEIG ERTMS USERS GROUP [¶38]

# 1.8.2 Chapter 1: Introduction [¶39]

- 1.8.2.1 Chapter 1 (this chapter) gives a general introduction to the intention and structure of the SRS, including a brief overview of the contents of each chapter. [¶40]

# 1.8.3 Chapter 2: Basic System Description [¶41]

- 1.8.3.1 Chapter 2 gives an overview of the ERTMS/ETCS system structure. [¶42]

- 1.8.3.2 Chapter 2 also contains a description of the basic application levels. [¶43]

- 1.8.3.3 Chapter 2 does not contain technical requirements. [¶44]

# 1.8.4 Chapter 3: Principles [¶45]

- 1.8.4.1 Chapter 3 specifies the system principles of ETCS/ERTMS. These principles apply to onboard and trackside subsystems. [¶46]

- 1.8.4.2 The principles define the behaviour of the system in general and functional terms. [¶47]

# 1.8.5 Chapter 4: Modes and Transitions [¶48]

- 1.8.5.1.1 Chapter  4  defines  the  modes  of  the  ERTMS/ETCS  onboard  equipment  and  all transitions between modes. [¶49]

# 1.8.6 Chapter 5: Procedures [¶50]

- 1.8.6.1 Chapter  5  defines  the  dynamic  behaviour  of  procedures  that  are  necessary  for interoperability. Procedures are presented by a state transition chart and a corresponding table, where all elements (States, events, transitions) of the chart are defined.  The  description  of  the  procedures  shows  all  states  of  the  ERTMS/ETCS onboard  unit  and  the  conditions  that  must  be  fulfilled  to  switch  from  one  state  to another. [¶51]

# 1.8.7 Chapter 6: Management of older System Versions [¶52]

- 1.8.7.1.1 Chapter  6  defines  the  envelope  of  legally  operated  system  versions  and  lists  the exceptions  that  shall  apply  by  derogation  to  the  requirements  listed  in  the  other chapters  of  the  SRS,  when  an  older  ERTMS/ETCS  system  version  is  used  by  the trackside subsystem. [¶53]

# 1.8.8 Chapter 7: ERTMS/ETCS Language [¶54]

- 1.8.8.1 Chapter 7 defines and describes the necessary variables to be used for the data flow over  the  air  gap  between  track  and  train.  The  grouping  of  these  into  packets  is described. The format of messages is given in Chapter 8. [¶55]


---
<!-- pagina 8 -->

# ERA * UNISIG * EEIG ERTMS USERS GROUP [¶56]

# 1.8.9 Chapter 8: Messages [¶57]

- 1.8.9.1 Chapter  8  defines  the  application  protocol  (format  and  content  of  messages,  logical sequence for radio) necessary to achieve technical interoperability. [¶58]

- 1.8.9.2 The  scope  of  this  chapter  is  limited  to  the  application  protocol  and  the  content  of messages. [¶59]

# 1.8.10 Chapter 9: Classification of the SRS clauses [¶60]

- 1.8.10.1 Chapter 9 encloses a classification into categories of all the clauses in the chapters 1 to 8 of the SRS. [¶61]

- 1.8.10.2 In  particular  to  assess  properly  the  compliance  of  an  ERTMS/ETCS  on-board equipment with the SRS, it identifies which clauses contain requirements allocated to the  ERTMS/ETCS  on-board  equipment  and  conversely  which  ones  do  not,  either because they  contain  requirements  allocated  to  the  ERTMS/ETCS  trackside  only  or because they are of another type. [¶62]
