"""Seed the B.Sc. Software Engineering curriculum, Summit University, Offa.

Source: Department of Software Engineering Student Handbook (2024-2028),
Chapter 16 — CCMAS Course Content. Section 16.1 is the 70% NUC CCMAS core;
Section 16.2 is the 30% university-developed content (SUN-* codes).

Semester assignment
-------------------
The handbook's tables are titled "FIRST AND SECOND SEMESTER" and do not split
the courses between them. Semesters are therefore derived from the university's
numbering policy — the last digit of the course number is odd for first-semester
courses and even for second-semester ones — which the published codes follow
consistently (GST111/GST112, MTH101/MTH102, PHY107/PHY108, COS201/COS202,
SEN497/SEN498). ``Course.save()`` re-derives it from the code on every write.

Known discrepancies inside the handbook itself, resolved as noted:
  * ENT211 vs ENT212 — Table 3.2 lists ENT212; the course synopsis is headed
    "ENT 211: Entrepreneurship and Innovation". ENT211 is used here: it matches
    the synopsis and the national CCMAS. Change to ENT212 to follow the table.
  * CSC203, IFT211, IFT212 — the tables give 2 units each, the synopses give 3.
    The table values are used because they are what make the 200-level total of
    28 units add up.
  * SUN-SFE204 — Table lists "Backend Technology 1"; the synopsis is headed
    "Frontend Technology II". The table title is used.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.courses.models import Course


GENERAL = "General"
COMPUTING = "Computer Science"      # shared computing core (COS/CSC/MTH/PHY/STA/INS/IFT)
SOFTWARE = "Software Engineering"   # SEN and SUN-SFE

# Handbook course status: C = Compulsory, R = Required, E = Elective.
# Only electives may be dropped without blocking graduation.
ELECTIVE = "E"

# (code, title, units, level, status, department, AR, LR, TK, QC, PA, description)
CURRICULUM = [
    # ══════════════════ 100 LEVEL — FIRST SEMESTER (odd codes) ══════════════
    ("GST111", "Communication in English", 2, 100, "C", GENERAL,
     5, 20, 40, 0, 35,
     "Sound patterns in English. Word classes and sentence structure. Grammar and "
     "usage. Logical and critical thinking and reasoning methods. Writing "
     "activities, comprehension strategies, public speaking and report writing."),

    ("MTH101", "Elementary Mathematics I (Algebra and Trigonometry)", 2, 100, "C", COMPUTING,
     20, 15, 15, 45, 5,
     "Elementary set theory, Venn diagrams. Real numbers, mathematical induction, "
     "sequences and series, quadratic equations, binomial theorem. Complex numbers "
     "and the Argand diagram. De-Moivre's theorem. Circular measure and "
     "trigonometric functions."),

    ("PHY101", "General Physics I (Mechanics)", 2, 100, "C", COMPUTING,
     10, 15, 25, 40, 10,
     "Space and time, units and dimensions. Vectors and scalars. Kinematics and "
     "Newton's laws of motion. Conservation principles. Rotational motion, torque "
     "and angular momentum. Moments of inertia. Gravitation and satellite motion."),

    ("PHY107", "General Practical Physics I", 1, 100, "C", COMPUTING,
     5, 10, 15, 30, 40,
     "Quantitative measurement, treatment of measurement errors and graphical "
     "analysis. Experiments on meters, the oscilloscope, mechanical and electrical "
     "resonant systems, light, heat and viscosity."),

    ("STA111", "Descriptive Statistics", 3, 100, "C", COMPUTING,
     10, 10, 15, 55, 10,
     "Statistical data: types, sources and methods of collection. Presentation of "
     "data in tables, charts and graphs. Frequency and cumulative distributions. "
     "Measures of location, partition, dispersion, skewness and kurtosis. Rates, "
     "ratios and index numbers."),

    ("COS101", "Introduction to Computing Sciences", 3, 100, "C", COMPUTING,
     10, 15, 35, 5, 35,
     "History of computing. Basic components of a computing device, input/output "
     "devices and peripherals. Hardware, software and humanware. Information "
     "processing and its role in society. The Internet and its impact. Areas of the "
     "computing discipline and job specialisations."),

    ("SUN-ICT101", "Introduction to Artificial Intelligence & Machine Learning", 2, 100, "C", GENERAL,
     30, 20, 25, 15, 10,
     "Definition and types of AI: rule-based systems, decision trees, neural "
     "networks. Machine learning algorithms: supervised, unsupervised and "
     "reinforcement learning. Model evaluation metrics. Ethics and social "
     "implications of AI including bias, privacy and job displacement."),

    ("SUN-ICT103", "Clean and Renewable Energy Systems", 2, 100, "C", GENERAL,
     10, 15, 35, 20, 20,
     "Fundamentals of electricity, generation, transmission and distribution. "
     "Renewable and clean energy systems. Solar energy for homes and off-grid "
     "installation. Smart solar energy systems and smart meters. Sustainable "
     "management of solar energy systems and the smart grid."),

    # ══════════════════ 100 LEVEL — SECOND SEMESTER (even codes) ════════════
    ("GST112", "Nigerian Peoples and Culture", 2, 100, "C", GENERAL,
     15, 10, 60, 0, 15,
     "Nigerian history, culture and art up to 1800. Nigeria under colonial rule and "
     "its evolution as a political unit. Challenges of nation building. Concept of "
     "trade and economics of self-reliance. Social justice and national "
     "development. Norms, values and re-orientation strategies."),

    ("MTH102", "Elementary Mathematics II (Calculus)", 2, 100, "C", COMPUTING,
     15, 10, 15, 55, 5,
     "Function of a real variable, graphs, limits and continuity. The derivative as "
     "limit of rate of change. Techniques of differentiation. Extreme curve "
     "sketching. Integration as the inverse of differentiation, methods of "
     "integration, definite integrals and application to areas and volumes."),

    ("PHY102", "General Physics II (Electricity and Magnetism)", 2, 100, "C", COMPUTING,
     10, 15, 25, 40, 10,
     "Electrostatics, Coulomb's law and superposition. Electric field, potential and "
     "Gauss's law. Capacitance and dielectrics. DC circuits and Ohm's law. Magnetic "
     "fields, Lorentz force, Biot-Savart and Ampere's laws. Electromagnetic "
     "induction, Faraday and Lenz's laws. Maxwell's equations."),

    ("PHY108", "General Practical Physics II", 1, 100, "C", COMPUTING,
     5, 10, 15, 30, 40,
     "Continuation of PHY107, covering the practical aspect of the second-semester "
     "theoretical courses with emphasis on quantitative measurement, treatment of "
     "measurement errors, graphical analysis and the preparation of practical "
     "reports."),

    ("COS102", "Introduction to Problem Solving", 3, 100, "C", COMPUTING,
     25, 35, 10, 10, 20,
     "Core concepts of computing. Identification and types of problems. Algorithms "
     "and heuristics. Solvable and unsolvable problems. Solution techniques: "
     "abstraction, analogy, brainstorming, hypothesis testing, reduction, means-end "
     "analysis, divide and conquer. Flowcharts, pseudocode, decision tables and "
     "trees. Programming in C or Python."),

    ("SUN-ICT102", "Current Trends in Artificial Intelligence & Machine Learning", 2, 100, "C", GENERAL,
     25, 15, 35, 15, 10,
     "Current trends and applications of AI and ML across business, finance, "
     "transportation, mass communication, education and the sciences. Practical "
     "applications and case studies. Evaluation and limitations of AI and ML "
     "systems. Careers in AI and related fields."),

    ("SUN-SFE104", "Software Development and Advancement", 1, 100, "C", SOFTWARE,
     10, 15, 20, 0, 55,
     "Modern software development methodologies and the software development life "
     "cycle. Programming languages, IDEs and version control systems. Agile and "
     "DevOps practices. Web and mobile application development. Data management, "
     "security, cloud computing and microservices."),

    # ══════════════════ 200 LEVEL — FIRST SEMESTER (odd codes) ══════════════
    ("ENT211", "Entrepreneurship and Innovation", 2, 200, "C", GENERAL,
     15, 15, 40, 10, 20,
     "Concept and theories of entrepreneurship and intrapreneurship. "
     "Characteristics of entrepreneurs. Entrepreneurial thinking. Innovation and "
     "its dimensions. Enterprise formation, partnership and networking. "
     "Contemporary entrepreneurship issues in Nigeria. Basic principles of "
     "e-commerce."),

    ("MTH201", "Mathematical Methods I", 2, 200, "C", COMPUTING,
     20, 10, 15, 50, 5,
     "Real-valued functions of a real variable. Review of differentiation and "
     "integration. Mean value theorem and Taylor series. Real-valued functions of "
     "two and three variables. Partial derivatives, chain rule, extrema, Lagrangian "
     "multipliers. Evaluation of line integrals and multiple integrals."),

    ("COS201", "Computer Programming I", 3, 200, "C", COMPUTING,
     20, 30, 10, 5, 35,
     "Essentials of computer programming and types of programming. Structured "
     "programming principles. Basic data types, variables, expressions and "
     "operators. Object-oriented concepts: abstraction, objects, classes, methods, "
     "parameter passing and encapsulation. Searching, sorting and recursive "
     "algorithms. Event-driven programming and exception handling."),

    ("SEN201", "Introduction to Software Engineering", 2, 200, "C", SOFTWARE,
     20, 20, 35, 5, 20,
     "Software engineering concepts and principles. Software processes: lifecycle "
     "and process models, process assessment and metrics. Software requirements and "
     "specification. Software design, architecture and validation. Software "
     "evolution, maintenance and reuse. Software project management. Software "
     "engineering and law."),

    ("CSC203", "Discrete Structures", 2, 200, "C", COMPUTING,
     30, 35, 10, 20, 5,
     "Propositional and predicate logic. Sets, functions, sequences and summation. "
     "Proof techniques and mathematical induction. Inclusion-exclusion and "
     "pigeonhole principles. Permutations and combinations. The binomial theorem. "
     "Discrete probability and recurrence relations."),

    ("IFT211", "Digital Logic Design", 2, 200, "C", COMPUTING,
     20, 35, 15, 20, 10,
     "Information representation and number systems. Boolean algebra and switching "
     "theory. Minimisation of Boolean functions. Physical properties of gates. "
     "Combinational circuit design using multiplexers, decoders, comparators and "
     "adders. Sequential circuit analysis, flip-flops, registers, counters, RAMs, "
     "ROMs, PLAs, PLDs and FPGAs."),

    ("SUN-ICT201", "History, Heritage and Story Telling", 2, 200, "C", GENERAL,
     15, 10, 55, 0, 20,
     "History, heritage and their role in shaping cultural identity and values. The "
     "impact of colonialism, imperialism and globalisation. Forms of storytelling "
     "and their relationship with memory. Techniques for effective storytelling and "
     "ethical considerations. Multimedia and infographic content generation."),

    ("SUN-SFE203", "Frontend Technology I", 2, 200, ELECTIVE, SOFTWARE,
     5, 15, 10, 0, 70,
     "Fundamentals of web design principles and user experience. HTML tags, "
     "attributes and forms with input validation. CSS selectors, layout, responsive "
     "design and pre-processors. Vanilla JavaScript and DOM manipulation. "
     "Bootstrap, Foundation and Materialize. Debugging, accessibility and "
     "performance. Version control with Git and GitHub."),

    # ══════════════════ 200 LEVEL — SECOND SEMESTER (even codes) ════════════
    ("GST212", "Philosophy, Logic and Human Existence", 2, 200, "C", GENERAL,
     30, 40, 25, 0, 5,
     "Scope, branches and problems of philosophy. Logic as an indispensable tool of "
     "philosophy. Elements of syllogism and symbolic logic — the first nine rules "
     "of inference. Informal fallacies and laws of thought. Valid and invalid "
     "arguments, deduction, induction and inference. Creative and critical "
     "thinking."),

    ("MTH202", "Mathematical Methods II", 2, 200, "C", COMPUTING,
     15, 10, 15, 55, 5,
     "Derivation of differential equations from primitives, geometry and physics. "
     "Order and degree of differential equations. Techniques for solving first and "
     "second order linear and non-linear equations. Solutions of systems of first "
     "order linear equations. Finite linear difference equations."),

    ("COS202", "Computer Programming II", 3, 200, "C", COMPUTING,
     25, 25, 10, 5, 35,
     "Advanced object-oriented programming: polymorphism, abstract classes and "
     "interfaces. Class hierarchies and programme organisation using packages. Use "
     "of API iterators, List, Stack and Queue. Searching, sorting and recursive "
     "algorithms. Event-driven programming and exception handling. Applications in "
     "Graphical User Interface programming."),

    ("INS204", "Systems Analysis and Design", 3, 200, "C", COMPUTING,
     25, 20, 15, 5, 35,
     "Structured approach to analysis and design of information systems. Software "
     "development life cycle. Top-down and bottom-up design. Dataflow diagramming "
     "and entity relationship modelling. Computer aided software engineering. "
     "Prototyping design and validation. File and database design. Design of user "
     "interfaces."),

    ("IFT212", "Computer Architecture and Organisation", 2, 200, "C", COMPUTING,
     15, 30, 25, 15, 15,
     "Instruction formats and types. Memory and I/O instructions, dataflow, "
     "arithmetic and flow control instructions. Addressing modes, stack operations "
     "and interrupts. Data path and control unit design. RTL, microprogramming and "
     "hardwired control. Assembly language programming. Memory hierarchy, cache "
     "and virtual memory."),

    ("SUN-ICT202", "Islam and Global Citizenship", 2, 200, "C", GENERAL,
     15, 15, 55, 0, 15,
     "The Islamic perspective on global citizenship and cultural/religious "
     "intelligence. Islamic values and principles in relation to contemporary "
     "global issues. Intercultural communication and collaboration. Religious "
     "diversity and social justice. Communication and leadership in a diverse and "
     "global context."),

    ("SUN-SFE204", "Backend Technology I", 2, 200, ELECTIVE, SOFTWARE,
     10, 20, 10, 5, 55,
     "Advanced HTML and CSS with semantic markup and accessibility best practices. "
     "CSS animation and effects. Advanced JavaScript: closures, prototypes and "
     "asynchronous programming. Single-page applications with Angular, React or "
     "Vue.js. REST APIs, status codes and data formats. Build systems, testing "
     "automation and deployment."),

    # ══════════════════ 200 LEVEL — LONG VACATION ═══════════════════════════
    ("SEN299", "Students Industrial Work Experience Scheme I", 3, 200, "C", SOFTWARE,
     5, 10, 15, 0, 70,
     "Three-month industrial attachment to a private or public organisation during "
     "the second-year long vacation, to acquire practical experience across all "
     "areas of Software Engineering. Students keep monitored records and submit and "
     "defend a report on the experience gained."),

    # ══════════════════ 300 LEVEL — FIRST SEMESTER (odd codes) ══════════════
    ("SEN301", "Object-Oriented Analysis and Design", 2, 300, "C", SOFTWARE,
     35, 20, 15, 0, 30,
     "Object-oriented approach to information system development. Importance and "
     "principles of modelling. Conceptual model of the Unified Modelling Language "
     "(UML), architecture and the software development life cycle. Use case, "
     "activity, class, state chart, component and deployment diagrams. UML-based "
     "CASE tools."),

    ("CSC301", "Data Structures", 3, 300, "C", COMPUTING,
     30, 30, 10, 15, 15,
     "Primitive types, arrays, records, strings and string processing. Data "
     "representation in memory. Stack and heap allocation. Queues and trees, and "
     "implementation strategies for them. Run-time storage management. Pointers, "
     "references and linked structures. Algorithm efficiency using big-O notation."),

    ("SUN-ICT301", "Acadopreneurship", 2, 300, "C", GENERAL,
     15, 15, 40, 10, 20,
     "Transforming academic ideas and research outputs into startups. Theory of "
     "acadopreneurship. Ideation and business planning, intellectual property "
     "protection and technology transfer. Entrepreneurial marketing, sales, finance "
     "and investment. The business model canvas. Implementation, scaling, and legal "
     "and ethical issues."),

    ("SUN-ICT303", "Family Skills for 21st Century Learners", 1, 300, "C", GENERAL,
     10, 10, 55, 0, 25,
     "The concept of family and its role in personal and social development. "
     "Dimensions of family life: relationships, communication and conflict "
     "resolution. Principles and practices of effective leadership: vision, "
     "strategy, motivation, decision-making, delegation and team-building. "
     "Leadership styles and their impact."),

    ("SUN-SFE305", "Programming with Python I", 2, 300, ELECTIVE, SOFTWARE,
     15, 25, 10, 5, 45,
     "History of Python and configuring the development environment. Basic data "
     "types and structures. Control structures. Functions, modules and packages. "
     "Object-oriented programming in Python: classes, encapsulation, inheritance "
     "and polymorphism. File handling and I/O. Error handling, assertions, unit "
     "tests and test-driven development."),

    ("SUN-SFE307", "Data Management I", 2, 300, ELECTIVE, SOFTWARE,
     20, 20, 25, 5, 30,
     "Information management concepts: storage, retrieval, capture and "
     "representation. Analysis and indexing, information privacy, integrity and "
     "security. Introduction to database systems and DBMS functions. Database "
     "architecture and data independence. Relational and semi-structured data "
     "models. Database design, query processing, concurrency and recovery."),

    # ══════════════════ 300 LEVEL — SECOND SEMESTER (even codes) ════════════
    ("GST312", "Peace and Conflict Resolution", 2, 300, "C", GENERAL,
     20, 20, 45, 0, 15,
     "Concepts of peace, conflict and security in a multi-ethnic nation. Types and "
     "theories of conflict. Root causes of conflict and violence in Africa. Peace "
     "building and management of conflict. Justice and legal frameworks. Insurgency "
     "and terrorism. Alternative dispute resolution. Roles of international "
     "organisations in conflict resolution."),

    ("ENT312", "Venture Creation", 2, 300, "C", GENERAL,
     15, 15, 30, 15, 25,
     "Opportunity identification and environmental scanning. New business "
     "development and market research. Entrepreneurial finance: venture capital, "
     "equity finance and microfinance. Entrepreneurial marketing and e-commerce. "
     "Small and family business management. Negotiation and business communication. "
     "Technological solutions and digital business strategies."),

    ("SEN304", "Software Testing and Quality Assurance", 2, 300, "C", SOFTWARE,
     10, 30, 20, 10, 30,
     "The importance of software testing. Verification and validation and the need "
     "for a culture of quality. Avoidance of errors and other quality problems. "
     "Inspections and reviews. Process assurance versus product assurance. Quality "
     "process standards. Statistical approaches to quality control. Unit, "
     "integration, system, performance, load, stress and security testing."),

    ("SEN306", "Software Construction", 2, 300, "C", SOFTWARE,
     15, 25, 10, 5, 45,
     "Definition and importance of software construction. Key construction "
     "decisions including choice of programming language. Design in construction, "
     "design heuristics and abstract data types. Working classes and high quality "
     "routines. The pseudo-code programming process. Types of statements. Developer "
     "testing, debugging and software craftsmanship."),

    ("SEN322", "Software Engineering Innovation and New Technology", 2, 300, "C", SOFTWARE,
     15, 15, 35, 10, 25,
     "The software entrepreneurial process and principles of software business "
     "ownership. Identifying software market opportunities. Entrepreneurial "
     "software marketing. Business communication and negotiation techniques. "
     "Feasibility analysis and entrepreneurial financing. Legal issues. Software "
     "business plan development and risk management."),

    ("CSC308", "Operating Systems", 3, 300, "C", COMPUTING,
     20, 30, 30, 10, 10,
     "Fundamentals of operating system design and implementation. History, "
     "evolution and types of operating systems. Operating system structures. "
     "Process management: processes, threads, CPU scheduling and process "
     "synchronisation. Memory management and virtual memory. File systems and I/O "
     "systems. Security, protection and distributed systems."),

    ("SUN-ICT302", "Basic Financial Literacy", 1, 300, "C", GENERAL,
     5, 15, 35, 30, 15,
     "Needs and wants and how to prioritise them. Managing money and keeping "
     "records; household versus business assets. Financial planning and budgeting. "
     "Savings options and savings plans. Borrowing: benefits, costs, risks and loan "
     "structuring. Forms of investment and monitoring. Financial fraud and scams "
     "and how to protect against them."),

    ("SUN-ICT304", "Leadership in the 21st Century for Scientist", 1, 300, "C", GENERAL,
     15, 15, 50, 0, 20,
     "Defining leadership and distinguishing it from management. Trait, "
     "behavioural, contingency, transformational and servant leadership theories. "
     "Leadership in a global context. Leadership communication. Emotional "
     "intelligence and self-awareness. Leadership ethics and values. Leading "
     "change. Team building and collaboration. Women in leadership."),

    ("SUN-SFE306", "Programming with Python II", 2, 300, ELECTIVE, SOFTWARE,
     20, 25, 10, 15, 30,
     "Advanced data structures and algorithms with time and space complexity "
     "analysis. Web development with Flask and Django, HTTP handling and RESTful "
     "APIs. Database programming and ORM frameworks. Concurrency and parallelism: "
     "threading, multiprocessing and asyncio. Data analysis with NumPy, Pandas and "
     "Matplotlib. Machine learning with scikit-learn and TensorFlow."),

    ("SUN-SFE308", "Mobile Application Technology", 2, 300, ELECTIVE, SOFTWARE,
     5, 15, 10, 0, 70,
     "Mobile application development for iOS and Android. Mobile user interface "
     "design and platform conventions. Working with device capabilities and remote "
     "APIs. Local storage and offline behaviour. Packaging, distribution and "
     "maintenance of mobile applications."),

    # ══════════════════ 300 LEVEL — LONG VACATION ═══════════════════════════
    ("SEN399", "Students Industrial Work Experience Scheme II", 3, 300, "C", SOFTWARE,
     5, 10, 15, 0, 70,
     "Three-month industrial attachment during the third-year long vacation, "
     "building additional practical experience across all areas of Software "
     "Engineering over and above SEN299. Students keep monitored records and submit "
     "and defend a report on the experience gained."),

    # ══════════════════ 400 LEVEL — FIRST SEMESTER (odd codes) ══════════════
    ("COS409", "Research Methodology and Technical Report Writing", 3, 400, "C", COMPUTING,
     20, 20, 40, 10, 10,
     "Foundations, types and approaches to research. Research methods versus "
     "methodology. Principles of scientific research and problem formulation. "
     "Developing research proposals and plans. Literature review. Elicitation "
     "techniques: questionnaires, interviewing and ethnography. System design and "
     "UML analysis. Technical report writing, citation and referencing."),

    ("SEN401", "Software Configuration Management and Maintenance", 2, 400, "C", SOFTWARE,
     15, 20, 25, 5, 35,
     "Management of the software configuration management process. Planning, the "
     "SCM plan and surveillance. Configuration identification and the software "
     "library. Configuration control: requesting, evaluating and approving changes. "
     "Status accounting and auditing. Key issues in software maintenance, cost "
     "estimation, re-engineering, reverse engineering, migration and retirement."),

    ("SEN497", "Final Year Student's Project I", 3, 400, "C", SOFTWARE,
     30, 20, 25, 10, 15,
     "An independent or group investigation addressing a Software Engineering "
     "problem under supervision. A written proposal is submitted before "
     "registration. The introduction, literature review and methodology are "
     "submitted for grading at the end of the semester, with an oral presentation "
     "where required."),

    ("INS401", "Project Management", 2, 400, "C", COMPUTING,
     15, 20, 35, 10, 20,
     "The project management lifecycle, context and processes. Managing project "
     "teams, communication and scope. Project scheduling techniques and common "
     "problems. Managing project resources, quality and risk. Project procurement, "
     "external acquisition and outsourcing. Project execution, control, closure and "
     "auditing."),

    ("SUN-CSC401", "Natural Language Processing I", 2, 400, "R", COMPUTING,
     30, 20, 20, 20, 10,
     "Overview of NLP and its applications. Basic linguistics: morphology, syntax "
     "and semantics. Text representation: tokenisation, stemming and lemmatisation. "
     "Language models and probability theory. Information retrieval and text "
     "classification. Named entity recognition and part-of-speech tagging. Machine "
     "translation. Sentiment analysis and conversational agents."),

    ("SUN-ICT403", "Grantsmanship in Industry 4.0 Technologies", 2, 400, "C", GENERAL,
     15, 15, 40, 10, 20,
     "Overview of the grant writing process and identifying funding opportunities. "
     "Developing a clear project concept and understanding the funder's "
     "perspective. Writing a persuasive proposal narrative supported by research "
     "and data. Creating a realistic budget. Effective communication with funders. "
     "Peer review and refinement before submission."),

    ("SUN-CSC405", "Optimization Techniques", 2, 400, "R", COMPUTING,
     20, 15, 10, 50, 5,
     "Concept and classification of optimisation problems. Linear programming: "
     "formulation, simplex method, duality, sensitivity analysis, transportation "
     "and assignment problems, network minimisation and shortest route. Queuing "
     "theory. Unconstrained and constrained optimisation. Robust optimisation, "
     "network flows, discrete, dynamic and nonlinear optimisation."),

    # ══════════════════ 400 LEVEL — SECOND SEMESTER (even codes) ════════════
    ("SEN410", "Software Architecture and Design", 2, 400, "C", SOFTWARE,
     40, 20, 20, 5, 15,
     "An in-depth look at software design. Design patterns, frameworks and "
     "architectures. Survey of current middleware architectures and design of "
     "distributed systems. Component based design. Measurement theory and the use "
     "of metrics in design. Designing for reliability, performance, safety, "
     "security and reusability. Evaluation and evolution of designs."),

    ("SEN498", "Final Year Student's Project II", 3, 400, "C", SOFTWARE,
     20, 20, 15, 10, 35,
     "Continuation of SEN497, containing the implementation and evaluation of the "
     "project. A formal written report covering chapters 4 and 5 is approved by the "
     "supervisor, and a final report comprising chapters 1 to 5 is submitted for "
     "final grading. An oral presentation is required."),

    ("SUN-CSC402", "Natural Language Processing II", 2, 400, "R", COMPUTING,
     30, 20, 15, 25, 10,
     "Advanced text classification: hierarchical, multi-label and deep "
     "learning-based. Sequence labelling with conditional random fields and hidden "
     "Markov models. Advanced text generation, neural machine translation and text "
     "style transfer. Coreference resolution. Discourse analysis. Text mining and "
     "topic modelling with LDA and NMF."),

    ("SUN-SYS404", "Human-Computer Interaction", 2, 400, ELECTIVE, COMPUTING,
     20, 15, 25, 0, 40,
     "Foundations of HCI and the concepts underlying its design. Principles of GUI "
     "and GUI toolkits. System design methods. User conceptual models and interface "
     "metaphors. Human cognitive and physical ergonomics. Human-centred software "
     "evaluation and development. GUI design, programming and practical evaluation."),

    ("SUN-CSC406", "System Reliability Test", 2, 400, "R", COMPUTING,
     15, 15, 15, 50, 5,
     "Concept of reliability and of probability in reliability. Failures and risks. "
     "Probability distributions for reliability. Failure types and causes, MTTF and "
     "MTBF, common mode failure and Failure Mode Effect Analysis. Reliability of "
     "series and parallel systems. Markov models. Fault tree and event tree "
     "analysis. Reliability in design and maintenance."),
]

# Long-vacation industrial attachments. They carry credit toward graduation but
# are not registered against a semester's 15-24 unit load, so the planner leaves
# them out of semester selection.
SIWES_CODES = {"SEN299", "SEN399"}

# The handbook publishes no prerequisite table. Only the dependencies it states
# outright in the course synopses are recorded here — nothing is inferred.
COURSE_REQUISITES = {
    "PHY108": ["PHY107"],      # "continuation of PHY 107"
    "COS202": ["COS201"],      # "Review and coverage of advanced OOP"
    "SEN399": ["SEN299"],      # "over and above what is gained in SEN 299"
    "SEN498": ["SEN497"],      # "This is a continuation of SEN 497"
    "SUN-SFE204": ["SUN-SFE203"],   # "build on Frontend Technology I"
    "SUN-SFE306": ["SUN-SFE305"],
    "SUN-CSC402": ["SUN-CSC401"],   # "builds on ... Natural Language Processing I"
}


def _semester(code):
    """Odd course number → first semester, even → second (university policy)."""
    return Course.semester_from_code(code)


class Command(BaseCommand):
    help = "Seed the Summit University Software Engineering CCMAS curriculum"

    @transaction.atomic
    def handle(self, *args, **options):
        wanted = {row[0] for row in CURRICULUM}
        retired = self._retire_courses_not_in(wanted)

        created = updated = 0
        for (code, title, units, level, status, dept,
             ar, lr, tk, qc, pa, description) in CURRICULUM:
            fields = dict(
                title=title,
                credit_units=units,
                level=level,
                semester=_semester(code),
                department_classification=dept,
                description=description,
                is_compulsory=(status != ELECTIVE),
                is_active=True,
                abstract_reasoning=ar,
                logical_reasoning=lr,
                theoretical_knowledge=tk,
                quantitative_calculation=qc,
                practical_application=pa,
                metadata={
                    "handbook_status": status,
                    "delivery": "siwes_long_vacation" if code in SIWES_CODES else "semester",
                    "source": "Summit University Offa, B.Sc. Software Engineering Handbook 2024-2028",
                },
            )
            course, was_created = Course.objects.get_or_create(code=code, defaults=fields)
            if was_created:
                created += 1
                continue
            changed = False
            for field, value in fields.items():
                if getattr(course, field) != value:
                    setattr(course, field, value)
                    changed = True
            if changed:
                course.save()
                updated += 1

        self._apply_prerequisites()

        self.stdout.write(self.style.SUCCESS(
            f"Software Engineering curriculum seeded: {created} created, "
            f"{updated} updated, {retired} retired "
            f"({Course.objects.filter(is_active=True).count()} active courses)."
        ))
        self._report_semester_loads()

    def _retire_courses_not_in(self, wanted):
        """Deactivate anything outside the handbook rather than deleting it.

        Students may hold transcript entries against previously seeded courses,
        so the rows have to survive; they simply stop being recommended.
        """
        stale = Course.objects.filter(is_active=True).exclude(code__in=wanted)
        count = stale.count()
        if count:
            stale.update(is_active=False)
        return count

    def _apply_prerequisites(self):
        codes = set(COURSE_REQUISITES) | {
            c for reqs in COURSE_REQUISITES.values() for c in reqs
        }
        courses = {c.code: c for c in Course.objects.filter(code__in=codes)}
        for code, prereq_codes in COURSE_REQUISITES.items():
            course = courses.get(code)
            if not course:
                continue
            course.prerequisites.clear()
            for prereq_code in prereq_codes:
                prereq = courses.get(prereq_code)
                if prereq:
                    course.prerequisites.add(prereq)

    def _report_semester_loads(self):
        """Print the registrable load per level/semester.

        The handbook requires 15-24 units per semester, but the published
        curriculum does not reach 15 in every semester once the courses are
        split by the odd/even numbering rule. Surfacing it here keeps the gap
        visible rather than letting it show up later as a student-facing error.
        """
        self.stdout.write("\nRegistrable units per semester (excludes SIWES):")
        short = []
        for level in (100, 200, 300, 400):
            for semester in (1, 2):
                units = sum(
                    row[2] for row in CURRICULUM
                    if row[3] == level and _semester(row[0]) == semester
                    and row[0] not in SIWES_CODES
                )
                flag = "" if units >= 15 else "   <-- below the 15-unit minimum"
                if units < 15:
                    short.append((level, semester, units))
                self.stdout.write(f"   {level} level, semester {semester}: {units:2} units{flag}")
        if short:
            self.stdout.write(self.style.WARNING(
                "\nThe handbook's tables do not state which semester each course "
                "falls in; the split above comes from the odd/even numbering rule. "
                "Confirm the department's actual split for the semesters flagged."
            ))
