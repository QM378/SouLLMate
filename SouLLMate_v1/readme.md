# SouLLMate - Your Personal Psychiatrist Assistant

SouLLMate is an advanced AI-powered platform designed to provide comprehensive psychiatric assistance. It offers personalized mental health support through various features including interactive conversations, assessments, and learning resources.

## Features

- Personalized interaction with AI
- Comprehensive mental health assessments
- Progress tracking and reporting
- Adaptive learning and goal setting
- Educational resources on mental health
- Profile management
- RAG (Retrieval-Augmented Generation) capabilities

## Prerequisites

- Anaconda or Miniconda
- Python 3.12

## Installation

1. Clone the repository:
conda env create -f environment.yml

2. Activate the environment:
conda activate chatbot


## Configuration

1. Set up your OpenAI API key:
- Open the `Config` class in the main script.
- Replace `"sk-proj-oSkM17wSZsVLuamHFtbRT3BlbkFJnzmw78p70EQ7lyByQb9T"` with your actual OpenAI API key.

2. Ensure you have the necessary folders:
- Create a folder named `Rag_document` in the project directory for RAG functionality.

## Running the Application

1. Make sure you're in the project directory and your conda environment is activated.

2. Run the main script:
python main.py

3. Open a web browser and navigate to `http://localhost:5006` to access the SouLLMate interface.

## Usage

- Register an account or log in to an existing one.
- Navigate through different tabs to access various features:
- Interactive Chat and Advisory
- Pre-Assessment
- Learn Psychology
- Practice Psych
- Suicide Risk Detection
- Report Generation
- RAG (Retrieval-Augmented Generation)
- And more...

## Key Components

- `UserManager`: Handles user registration, login, and profile management.
- `PDFProcessor`: Processes various document formats including PDFs.
- `LangchainManager`: Manages language model interactions and generates responses.
- `SuicideDetector`: Analyzes text for potential suicide risk.
- `ReportGenerator`: Creates comprehensive reports based on user data.
- `RAGManager`: Implements Retrieval-Augmented Generation for enhanced responses.
- `UIManager`: Manages the user interface and interactions.

## Note

This application is for educational and demonstration purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment.

## License

[GPL-3.0 license: https://github.com/QM378/SouLLMate/blob/main/LICENSE]

## Contact

For support or inquiries, please contact [guoqm07@gmail.com, tangjw91@gmail.com].

## Acknowledgments

This project uses various open-source libraries and AI models. We thank the developers and contributors of these technologies for their work.

## Contributing

Contributions to SouLLMate are welcome. Please feel free to submit pull requests or open issues to improve the functionality or documentation of the project.
