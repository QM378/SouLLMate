import os
import openai
import datetime
import json
import os
import tempfile
import pandas as pd
import random
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain, ConversationChain
from langchain.memory import ConversationBufferMemory
import panel as pn
pn.extension(notifications=True)
import tempfile
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredFileLoader
from PIL import Image
import pytesseract
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime
import base64
import docx2txt
from datetime import datetime
import json
from langchain_core.messages import SystemMessage
from datetime import date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors

Base = declarative_base()

class Config:
    def __init__(self):
        os.environ["OPENAI_API_KEY"] = "Your Api Key"
        openai.api_key = os.environ["OPENAI_API_KEY"]

class UserManager:
    def __init__(self):
        self.engine = create_engine('sqlite:///users.db', echo=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.current_user_id = None

    def register_user(self, username, password, nickname, email):
        session = self.Session()
        try:
            if session.query(User).filter_by(username=username).first():
                return False, "Username already exists."
            new_user = User(username=username, password=password, nickname=nickname, email=email)
            session.add(new_user)
            session.commit()
            return True, "Registration successful."
        except Exception as e:
            session.rollback()
            return False, f"Registration failed: {str(e)}"
        finally:
            session.close()

    def login_user(self, username, password):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user and user.password == password:
                user.login_time = datetime.now()
                session.commit()
                self.current_user_id = user.id

                session.refresh(user)
                return True, "Login successful."
            return False, "Invalid username or password."
        finally:
            session.close()


    def save_rag_document(self, username, document_data):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                if user.rag_documents is None:
                    user.rag_documents = []
                user.rag_documents.append(document_data)
                session.commit()
                return True, "RAG document saved successfully."
            return False, "User not found."
        except Exception as e:
            session.rollback()
            return False, f"Failed to save RAG document: {str(e)}"
        finally:
            session.close()

    def get_rag_documents(self, username):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                return user.rag_documents
            return None
        finally:
            session.close()

    def get_current_user(self):
        if self.current_user_id:
            session = self.Session()
            try:
                user = session.query(User).get(self.current_user_id)
                session.refresh(user)  
                return user
            finally:
                session.close()
        return None

    def logout_user(self):
        if self.current_user_id:
            self.current_user_id = None
            return True, "Logout successful."
        return False, "No user currently logged in."

    def get_user_data(self, username):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            return user.to_dict() if user else None
        finally:
            session.close()

    def save_user_data(self, username, data):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                for key, value in data.items():
                    setattr(user, key, value)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def update_user_profile(self, username, nickname, email, interests, mental_state):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                user.nickname = nickname
                user.email = email
                user.interests = interests
                user.mental_state = mental_state
                session.commit()
                return True, "Profile updated successfully."
            return False, "User not found."
        except Exception as e:
            session.rollback()
            return False, f"Profile update failed: {str(e)}"
        finally:
            session.close()

    def add_intervention_history(self, username, intervention_data):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                if user.intervention_history is None:
                    user.intervention_history = []
                user.intervention_history.append(intervention_data)
                session.commit()
                return True, "Intervention history added successfully."
            return False, "User not found."
        except Exception as e:
            session.rollback()
            return False, f"Failed to add intervention history: {str(e)}"
        finally:
            session.close()

    def update_mental_state(self, username, mental_state):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                user.mental_state = mental_state
                session.commit()
                return True, "Mental state updated successfully."
            return False, "User not found."
        except Exception as e:
            session.rollback()
            return False, f"Mental state update failed: {str(e)}"
        finally:
            session.close()

    def add_exam_history(self, username, exam_data):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                if user.exam_history is None:
                    user.exam_history = [exam_data]
                else:
                    user.exam_history.append(exam_data)
                session.commit()
                print(f"Exam history added and committed for user {username}: {exam_data}")
                return True, "Exam history added successfully."
            return False, "User not found."
        except Exception as e:
            session.rollback()
            print(f"Error adding exam history: {str(e)}")
            return False, f"Failed to add exam history: {str(e)}"
        finally:
            session.close()

    def add_study_material(self, username, material):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                if user.study_materials is None:
                    user.study_materials = []
                user.study_materials.append(material)
                session.commit()
                return True, "Study material added successfully."
            return False, "User not found."
        except Exception as e:
            session.rollback()
            return False, f"Failed to add study material: {str(e)}"
        finally:
            session.close()

    def add_practice_history(self, username, practice_data):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                if user.practice_history is None:
                    user.practice_history = []
                user.practice_history.append(practice_data)
                session.commit()
                return True, "Practice history added successfully."
            return False, "User not found."
        except Exception as e:
            session.rollback()
            return False, f"Failed to add practice history: {str(e)}"
        finally:
            session.close()

    def save_user_notes(self, username, notes):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                user.notes = notes
                session.commit()
                return True, "Notes saved successfully."
            return False, "User not found."
        except Exception as e:
            session.rollback()
            return False, f"Failed to save notes: {str(e)}"
        finally:
            session.close()

    def get_user_notes(self, username):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                return user.notes
            return None
        finally:
            session.close()

    def add_learning_history(self, username, learning_content):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                if user.study_materials is None:
                    user.study_materials = []
                user.study_materials.append({
                    'content': learning_content,
                    'timestamp': datetime.now().isoformat()
                })
                session.commit()
                return True, "Learning history added successfully."
            return False, "User not found."
        except Exception as e:
            session.rollback()
            return False, f"Failed to add learning history: {str(e)}"
        finally:
            session.close()

    def get_learning_history(self, username):
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                return user.study_materials
            return None
        finally:
            session.close()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    nickname = Column(String)
    email = Column(String)
    role = Column(String, default='student')
    login_time = Column(DateTime)
    interests = Column(Text)
    mental_state = Column(Text)
    intervention_history = Column(JSON)
    questions = Column(JSON)
    answers = Column(JSON)
    evaluations = Column(JSON)
    weaknesses = Column(JSON)
    exam_history = Column(JSON)
    study_materials = Column(JSON) 
    practice_history = Column(JSON)
    notes = Column(Text)
    rag_documents = Column(JSON)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "email": self.email,
            "role": self.role,
            "login_time": self.login_time,
            "interests": self.interests,
            "mental_state": self.mental_state,
            "questions": self.questions,
            "answers": self.answers,
            "evaluations": self.evaluations,
            "weaknesses": self.weaknesses,
            "intervention_history": self.intervention_history,
            "exam_history": self.exam_history,
            "study_materials": self.study_materials,
            "practice_history": self.practice_history,
            "notes": self.notes,
            "rag_documents": self.rag_documents
        }



class PDFProcessor:
    @staticmethod
    def load_and_process_pdf(file_path):
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()

        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            return ' '.join([page.page_content for page in pages])

        elif file_extension in ['.doc', '.docx']:
            loader = Docx2txtLoader(file_path)
            pages = loader.load()
            return ' '.join([page.page_content for page in pages])

        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text

        else:
            loader = UnstructuredFileLoader(file_path)
            pages = loader.load()
            return ' '.join([page.page_content for page in pages])


class SuicideDetector:
    def __init__(self, llm_name="gpt-4"):
        self.llm = ChatOpenAI(model_name=llm_name, temperature=0)
        self.templates = {
            'suicide_intent': """
    Read the given conversation between AI and human and determine if it indicates the human has suicidal intent. Select the most appropriate number (0 or 1) from the following options:
    -0: No, it does not indicate the human has suicidal intent.
    -1: Yes, it indicates the human has suicidal intent.
    
    Here is the conversation: <Conversation> {input} <Conversation>.
    The response should be numeric (0 or 1).
    """,
            'suicide_phrase': """
    Read the given conversation between AI and human. Identify and list any words or phrases which can indicate this human has suicidal ideation, method, plan, or intent. If the conversation does not contain any relevant words, please type "NA".

    Here is the conversation: <Conversation> {input} <Conversation>.
    The response should be a list of words or phrases separated by commas.
    """,
            'Passive_Ideation': """
    Read the given conversation between AI and human and determine if it indicates this human has passive suicidal ideation (wish to be dead). Select the most appropriate number (0 or 1) from the following options:
    -0: No, it does not indicate this human has passive suicidal ideation.
    -1: Yes, it indicates this human has passive suicidal ideation.
    
    Here is the conversation: <Conversation> {input} <Conversation>.
    The response should be numeric (0 or 1).
    """,
            'Active_Ideation': """
    Read the given conversation between AI and human and determine if it indicates this human has active suicidal ideation (non-specific active suicidal thoughts, no method, intent, or plan). Select the most appropriate number (0 or 1) from the following options:
    -0: No, it does not indicate this human has active suicidal ideation.
    -1: Yes, it indicates this human has active suicidal ideation.
    
    Here is the conversation: <Conversation> {input} <Conversation>.
    The response should be numeric (0 or 1).
    """,
            'Intent': """
    Read the given conversation between AI and human and determine if it indicates this human has active suicidal ideation with some intent to act, without a specific plan. Select the most appropriate number (0 or 1) from the following options:
    -0: No, it does not indicate this human has active suicidal ideation with some intent to act.
    -1: Yes, it indicates this human has active suicidal ideation with some intent to act.
    
    Here is the conversation: <Conversation> {input} <Conversation>.
    The response should be numeric (0 or 1).
    """,
            'Plan': """
    Read the given conversation between AI and human and determine if it indicates this human has active suicidal ideation with a specific plan and intent. Select the most appropriate number (0 or 1) from the following options:
    -0: No, it does not indicate this human has active suicidal ideation with a specific plan and intent.
    -1: Yes, it indicates this human has active suicidal ideation with a specific plan and intent.
    
    Here is the conversation: <Conversation> {input} <Conversation>.
    The response should be numeric (0 or 1).
    """,
            'Behavior': """
    Read the given conversation between AI and human and determine if it indicates this human has engaged in self-harm or suicidal behavior or attempt. Select the most appropriate number (0 or 1) from the following options:
    -0: No, it does not indicate this human has engaged
    -1: in self-harm or suicidal behavior.

    Here is the conversation: <Conversation> {input} <Conversation>.
    The response should be numeric (0 or 1).
    """,
            'Supportive': """
    Read the given conversation between AI and human and determine if it indicates this human has received emotional, practical, or motivational support from others. Emotional support refers to expressions of empathy, understanding, and care. Practical support includes specific advice or actions aimed at solving problems. Motivational support involves encouragement and positive reinforcement. Select the most appropriate number (0 or 1) from the following options:
    -0: No, it does not indicate this human has received support from others.
    -1: Yes, it indicates this human has received support from others.
    
    Here is the conversation: <Conversation> {input} <Conversation>.
    The response should be numeric (0 or 1).
    """
        }

    def load_data(self, file_path):
        return pd.read_json(file_path)

    def generate_response(self, template, input_text):
        formatted_template = template.format(input=input_text)
        chat_template = ChatPromptTemplate.from_messages([
            SystemMessage(content=formatted_template)
        ])
        prompt = chat_template.format()
        response = self.llm.invoke(prompt)
        return response.content

    def process_dataframe(self, df):
        for column, template in self.templates.items():
            df[column] = df['chat_history'].apply(lambda x: self.generate_response(template, x))
        df['generated_results'] = df.apply(lambda row: {
            column: row[column] for column in self.templates.keys()
        }, axis=1)
        df = df.drop(columns=self.templates.keys())
        return df

    def save_dataframe(self, df, file_path):
        result = df.to_dict(orient='records')
        with open(file_path, 'w') as f:
            json.dump(result, f, indent=2, default=self.json_serial)
        print(f"Processing complete. The new file has been saved as '{file_path}'.")

    @staticmethod
    def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

class ReportGenerator:
    def __init__(self, llm_name="gpt-4"):
        self.llm = ChatOpenAI(model_name=llm_name, temperature=0)
        self.report_template = """
    For a given dataframe, please generate a report that includes the following information:

    1. <Suicide Intention Assessment> section: Provide a summary of this person's suicide intention based on the data. Explain why this assessment was made in a friendly and conversational way, as if you were talking directly to the person but do not mention who you are at any places. Avoid using tables or scores. Use easy-to-understand language so that anyone can comprehend. Use a supportive and empathetic tone to reduce social stigma. In this dataframe:
    - Passive_Ideation indicates a wish to be dead.
    - Active_Ideation indicates active suicidal ideation (non-specific active suicidal thoughts, no intent, or plan).
    - Intent indicates active suicidal ideation with some intent to act, without a specific plan.
    - Plan indicates active suicidal ideation with a specific plan and intent.
    - Behavior indicates self-harm or suicidal behavior or attempt.
    - Supportive indicates received emotional, practical, or motivational support from others
    
    A value of 1 indicates "yes," and a value of 0 indicates "no."

    2. If this person shows any signs of suicidal tendency, kindly offer some friendly suggestions for coping under <Coping Strategy> section using numerical bullet points. This could include activities like talking to a trusted friend, engaging in a favorite hobby, or practicing relaxation techniques. If there is no signs of suicidal tendency in dataframe, do not include this section.

    3. If this person shows any signs of suicidal tendency, provide some resources they can seek help from under <Resources> section using numerical bullet points. Mention hotlines, counseling services, or online support groups in a supportive and approachable manner (e.g., 988 Suicide & Crisis Lifeline, nearest hospital emergency room). If there is no signs of suicidal tendency in dataframe, do not include this section.

    Here is the dataframe: <Dataframe> {input} <Dataframe>.
    """

    def generate_report(self, df):
        df_string = df.to_string()
        formatted_template = self.report_template.format(input=df_string)
        chat_template = ChatPromptTemplate.from_messages([
            SystemMessage(content=formatted_template)
        ])
        prompt = chat_template.format()
        response = self.llm.invoke(prompt)
        return response.content

    def save_report(self, report: str, file_path: str, username: str) -> None:
        """Save the report to a well-formatted PDF file."""

        class FooterCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                canvas.Canvas.__init__(self, *args, **kwargs)
                self.pages = []

            def showPage(self):
                self.pages.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                page_count = len(self.pages)
                for page in self.pages:
                    self.__dict__.update(page)
                    self.draw_footer(page_count)
                    canvas.Canvas.showPage(self)
                canvas.Canvas.save(self)

            def draw_footer(self, page_count):
                self.setFont("Helvetica", 9)
                self.setFillColor(colors.HexColor("#666666"))
                
                page_width, page_height = letter
                right_margin = 72
                bottom_margin = 50
                footer_offset = 0
                
                # Page number
                page_num = f"Page {self._pageNumber} of {page_count}"
                self.drawRightString(page_width - right_margin, bottom_margin + footer_offset + 12, page_num)
                
                # Footer text and date
                footer_text = "SouLLMate - Your Personal Mental Health Assistant"
                date_text = date.today().strftime("%B %d, %Y")
                self.drawString(right_margin, bottom_margin + footer_offset + 12, footer_text)
                self.drawString(right_margin, bottom_margin + footer_offset, date_text)
                
                # Line
                self.setStrokeColor(colors.HexColor("#666666"))
                self.line(right_margin, bottom_margin + footer_offset + 24, 
                        page_width - right_margin, bottom_margin + footer_offset + 24)
                
                # Image
                img_path = "/home/jt/jt_proj/mental/gq_shared/AI.jpg"
                img_width = 0.5 * inch  # Reduced size
                img_height = 0.5 * inch  # Reduced size
                img_x = page_width - right_margin - img_width
                img_y = bottom_margin + footer_offset
                
                if os.path.exists(img_path):
                    self.drawImage(img_path, img_x, img_y, width=img_width, height=img_height)
                else:
                    print(f"Warning: Image file {img_path} not found.")



        doc = SimpleDocTemplate(file_path, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=50)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CustomHeading', 
                                  fontSize=16, 
                                  textColor=colors.HexColor("#1C4587"),  # Dark Blue
                                  fontName='Helvetica-Bold',
                                  spaceAfter=12))
        styles.add(ParagraphStyle(name='CustomBody', 
                                  fontSize=11, 
                                  leading=14, 
                                  alignment=TA_JUSTIFY,
                                  spaceAfter=8,
                                  textColor=colors.HexColor("#333333"),  # Dark Grey
                                  fontName='Helvetica'))
        styles.add(ParagraphStyle(name='CustomTitle', 
                                  fontSize=24, 
                                  alignment=TA_CENTER,
                                  textColor=colors.HexColor("#1C4587"), # Dark Blue
                                  fontName='Helvetica-Bold',
                                  spaceAfter=20))
        styles.add(ParagraphStyle(name='CustomSubHeading', 
                                  fontSize=14, 
                                  textColor=colors.HexColor("#3D85C6"),  # Light Blue
                                  fontName='Helvetica-Bold',
                                  spaceAfter=10))

        story = []

        # Add title
        story.append(Paragraph("Your Private Assessment Report", styles['CustomTitle']))
        story.append(Spacer(1, 24))

        # Replace [username] with actual username
        report = report.replace('[username]', username)

        # Split the report into paragraphs
        paragraphs = report.split('\n')

        for para in paragraphs:
            para = para.strip()
            if para.startswith('Report:'):
                story.append(Paragraph(para, styles['CustomHeading']))
            elif para:
                story.append(Paragraph(para, styles['CustomBody']))
            if para:
                story.append(Spacer(1, 6))

        doc.build(story, canvasmaker=FooterCanvas)
        print(f"Processing complete. The report has been saved as '{file_path}'.")

class LangchainManager:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.9, model="gpt-3.5-turbo")
        self.memory = ConversationBufferMemory(return_messages=True)
        self.conversation_chain = ConversationChain(llm=self.llm, memory=self.memory, verbose=True)
        self.suicide_detector = SuicideDetector() 

    def generate_summary(self, page_content):
        summary_prompt = ChatPromptTemplate.from_template(
            "Please summarize the following PDF content:  \n\n {pdf_content}?"
        )
        chain = LLMChain(llm=self.llm, prompt=summary_prompt)
        return chain.invoke(input={"pdf_content": page_content})['text']


    def generate_learning_content(self, learning_plan, current_progress):
        learning_content_prompt = ChatPromptTemplate.from_template(
            "Based on the following learning plan and current progress, generate the next part of learning content:\n\nLearning Plan: {learning_plan}\n\nCurrent Progress: {current_progress}\n\nGenerate about 300 words of learning content."
        )
        chain = LLMChain(llm=self.llm, prompt=learning_content_prompt)
        return chain.invoke(input={"learning_plan": learning_plan, "current_progress": current_progress})['text']
    

    def generate_response(self, template, input_text):
        formatted_template = template.format(input=input_text)
        chat_template = ChatPromptTemplate.from_messages([
            SystemMessage(content=formatted_template)
        ])
        prompt = chat_template.format()
        response = self.llm.invoke(prompt)
        return response.content


    def datetime_to_string(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    def generate_exam_question(self, pdf_summary):
        exam_question_prompt = ChatPromptTemplate.from_template(
            "Based on the following summary, generate two detailed test questions to assess students' understanding of the content. Ensure the questions are clear, specific, and directly related to the summary:\n\n{pdf_summary}"
        )
        chain = LLMChain(llm=self.llm, prompt=exam_question_prompt)
        return chain.invoke(input={"pdf_summary": pdf_summary})['text']

    def evaluate_student_answer(self, student_name, pdf_exam_question, answer):
        evaluation_prompt = ChatPromptTemplate.from_template(
            "please evaluate the student's performance. The score should be out of 100. Provide a detailed assessment including the student's score, areas where they lack understanding, and suggestions for improvement. Include the student's name {student_name}in the first row. The length of the assessment should be controlled to around 200 words.\n Based on the following questions \n {pdf_exam_question} \n and students answer1: \n {answer1} \n and \n answer2:\n  {answer2} "
        )
        chain = LLMChain(llm=self.llm, prompt=evaluation_prompt)
        return chain.invoke(input={
            "student_name": student_name,
            "pdf_exam_question": pdf_exam_question,
            "answer1": answer,
            "answer2": ""
        })['text']

    def generate_weakness_explanation(self, performance_evaluation):
        weakness_prompt = ChatPromptTemplate.from_template(
            "Based on the student's performance evaluation:\n\n{performance_evaluation}\n\nBriefly identify the student's main weaknesses and provide a concise explanation to help them improve. Limit your response to 50-100 words."
        )
        chain = LLMChain(llm=self.llm, prompt=weakness_prompt)
        result = chain.invoke(input={"performance_evaluation": performance_evaluation})['text']
        print(f"Generated weakness explanation: {result}")  
        return result

    def chat_response(self, user_input):
        response = self.conversation_chain.predict(input=user_input)
        
        risk_result = self.suicide_detector.process_dataframe(pd.DataFrame({'chat_history': [user_input]}))
        risk_level = risk_result['generated_results'].iloc[0]['suicide_intent']
        
        if risk_level == 1:
            response += "\n\nI've noticed some concerning content in our conversation. If you're feeling overwhelmed or having thoughts of self-harm, please reach out to a mental health professional or call a suicide prevention hotline. Your life matters, and help is available."
        
        return response

    def generate_study_material(self, weakness):
        study_material_prompt = ChatPromptTemplate.from_template(
            "Based on the following weakness: {weakness}, provide study material of 400-500 words to help improve understanding."
        )
        chain = LLMChain(llm=self.llm, prompt=study_material_prompt)
        return chain.invoke(input={"weakness": weakness})['text']

    def generate_practice_question(self, topic):
        practice_question_prompt = ChatPromptTemplate.from_template(
            "Generate a practice question related to the following topic: {topic}"
        )
        chain = LLMChain(llm=self.llm, prompt=practice_question_prompt)
        return chain.invoke(input={"topic": topic})['text']

    def evaluate_practice_answer(self, question, answer):
        evaluation_prompt = ChatPromptTemplate.from_template(
            "Evaluate the following answer to the question. Provide an explanation and an assessment, separated by a newline:\nQuestion: {question}\nAnswer: {answer}"
        )
        chain = LLMChain(llm=self.llm, prompt=evaluation_prompt)
        return chain.invoke(input={"question": question, "answer": answer})['text']

    def generate_learning_plan(self, user_data):
            # Convert datetime objects to strings
            serializable_data = {k: self.datetime_to_string(v) for k, v in user_data.items()}
            
            learning_plan_prompt = ChatPromptTemplate.from_template(
                "Based on the following user data, generate a personalized learning plan and learning goals:\n\n{user_data}\n\nProvide a detailed learning plan and a set of learning goals."
            )
            chain = LLMChain(llm=self.llm, prompt=learning_plan_prompt)
            return chain.invoke(input={"user_data": json.dumps(serializable_data)})['text']
    
    def generate_personal_psychology(self, mental_state):
        personal_psych_prompt = ChatPromptTemplate.from_template(
            "Based on the user's mental state: {mental_state}, generate a learning plan about psychology that would help them understand their condition better. Include relevant theories, coping strategies, and self-help techniques."
        )
        chain = LLMChain(llm=self.llm, prompt=personal_psych_prompt)
        return chain.invoke(input={"mental_state": mental_state})['text']

    def generate_general_psychology(self):
        general_psych_prompt = ChatPromptTemplate.from_template(
            "Generate a general learning plan about psychology, covering major topics such as cognitive psychology, developmental psychology, social psychology, and abnormal psychology. Include key theories and concepts."
        )
        chain = LLMChain(llm=self.llm, prompt=general_psych_prompt)
        return chain.invoke(input={})['text']

class RAGManager:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def load_documents(self):
        documents = []
        for filename in os.listdir(self.folder_path):
            if filename.endswith(('.pdf', '.doc', '.docx', '.txt')):
                file_path = os.path.join(self.folder_path, filename)
                content = self.load_document_content(file_path)
                documents.append({'filename': filename, 'content': content})
        return documents

    def load_document_content(self, file_path):

        return PDFProcessor.load_and_process_pdf(file_path)

    def search_similar_documents(self, query, documents, k=5):

        query_words = set(query.lower().split())
        scored_docs = []
        for doc in documents:
            doc_words = set(doc['content'].lower().split())
            similarity = len(query_words.intersection(doc_words)) / len(query_words.union(doc_words))
            scored_docs.append((similarity, doc))
        scored_docs.sort(reverse=True)
        return [doc for _, doc in scored_docs[:k]]


class UIManager:
    def __init__(self, user_manager, pdf_processor, langchain_manager, suicide_detector, report_generator, rag_manager):
        self.user_manager = user_manager
        self.pdf_processor = pdf_processor
        self.langchain_manager = langchain_manager
        self.suicide_detector = suicide_detector
        self.report_generator = report_generator
        self.rag_manager = rag_manager  
        self.js_pane = pn.pane.HTML(visible=False, width=0, height=0, margin=0)
        self.setup_ui_components()


        self.suicide_detection_input = pn.widgets.TextAreaInput(name="Chat History", placeholder="Enter chat history for suicide risk detection")
        self.suicide_detection_button = pn.widgets.Button(name="Detect Suicide Risk", button_type="primary")
        self.suicide_detection_output = pn.widgets.StaticText(name="Suicide Risk Detection Result")

        self.generate_report_button = pn.widgets.Button(name="Generate Report", button_type="primary")
        self.report_output = pn.widgets.StaticText(name="Generated Report")


        self.learning_content_output = pn.widgets.StaticText(name="Learning Content")
        self.continue_learning_button = pn.widgets.Button(name="Continue Learning", button_type="primary")
        self.view_history_button = pn.widgets.Button(name="View Learning History", button_type="primary")
        self.tabs = pn.Tabs()\
        
        self.start_practice_button = pn.widgets.Button(name="Start Practice", button_type="primary")
        self.start_mental_state_practice_button = pn.widgets.Button(name="Start Practice on Mental State", button_type="primary")
        self.start_random_practice_button = pn.widgets.Button(name="Start Random Practice", button_type="primary")
 

        self.understand_self_button = pn.widgets.Button(name="Understand Yourself", button_type="primary")
        self.understand_general_psych_button = pn.widgets.Button(name="Learn General Psychology", button_type="primary")
        self.psychology_output = pn.widgets.StaticText(name="Psychology Knowledge")


        self.rag_folder_input = pn.widgets.TextInput(name="RAG Folder Path", placeholder="Enter folder path")
        self.load_rag_folder_button = pn.widgets.Button(name="Load RAG from Folder", button_type="primary")
        self.rag_file_input = pn.widgets.FileInput(accept='.pdf,.doc,.docx,.txt')
        self.load_rag_file_button = pn.widgets.Button(name="Load RAG File", button_type="primary")
        self.rag_query_input = pn.widgets.TextInput(name="RAG Query", placeholder="Enter your query")
        self.rag_query_button = pn.widgets.Button(name="Search", button_type="primary")
        self.rag_output = pn.widgets.StaticText(name="RAG Output")

        self.understand_self_button.on_click(self.generate_personal_psychology)
        self.understand_general_psych_button.on_click(self.generate_general_psychology)

        self.suicide_detection_button.on_click(self.detect_suicide_risk)
        self.generate_report_button.on_click(self.generate_report)

        self.load_rag_folder_button.on_click(self.load_rag_from_folder)
        self.load_rag_file_button.on_click(self.load_rag_file)
        self.rag_query_button.on_click(self.perform_rag_query)

        self.continue_learning_button.on_click(self.continue_learning)
        self.view_history_button.on_click(self.view_learning_history)
        self.predefined_prompt = """You are a professional psychiatrist assistant named SouLLMate. Your role is to provide empathetic, supportive, and insightful responses to users seeking mental health advice or emotional support. Always maintain a compassionate and non-judgmental tone. If you suspect the user is in immediate danger or crisis, kindly suggest they seek immediate professional help. Remember, you're here to listen, support, and guide, but not to diagnose or replace professional medical advice. Now, please respond to the following user input:
        """

        
        # assessment
        self.document_assessment_prompt = """You are a professional psychiatrist. Analyze the following document and provide a comprehensive psychological assessment. Focus on identifying potential mental health issues, emotional states, and behavioral patterns. Provide a score from 1 to 10 for overall mental well-being, where 1 is extremely concerning and 10 is excellent. Include brief explanations for your assessment and recommendations for further steps or support.
        Document content:
        {document_content}
        Please provide your assessment:"""


        self.chat_assessment_prompt = """You are a professional psychiatrist conducting a psychological assessment through dialogue. Ask one relevant question at a time to understand the user's mental state, emotional well-being, and any potential issues. Do not simulate a full conversation. Only provide your next question or response based on the user's latest input. Remember any important information the user provides, such as their name.

        Current conversation:
        {conversation_history}

        Please provide your next question or response:"""

        self.profile_mental_state_input = pn.widgets.TextAreaInput(name="Mental State", placeholder="Your current mental state")
        self.intervention_chat_input = pn.widgets.TextAreaInput(name="Chat Input", placeholder="Enter your message", height=100)
        self.intervention_chat_button = pn.widgets.Button(name="Send", button_type="primary")
        self.intervention_chat_display = pn.pane.HTML(name="Chat Display", sizing_mode='stretch_width')
        self.intervention_chat_button.on_click(self.on_intervention_chat_submit)



    def load_rag_from_folder(self, event):
        documents = self.rag_manager.load_documents()
        self.save_rag_documents(documents)
        self.rag_output.value = "Documents loaded successfully from folder."

    def load_rag_file(self, event):
        if self.rag_file_input.value is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(self.rag_file_input.filename)[1]) as temp_file:
                temp_file.write(self.rag_file_input.value)
                temp_file_path = temp_file.name
            content = self.rag_manager.load_document_content(temp_file_path)
            document = {'filename': self.rag_file_input.filename, 'content': content}
            self.save_rag_documents([document])
            self.rag_output.value = "File loaded successfully."
            os.unlink(temp_file_path)
        else:
            self.rag_output.value = "Please select a file to upload."

    def perform_rag_query(self, event):
        query = self.rag_query_input.value
        if query:
            current_user = self.user_manager.get_current_user()
            if current_user:
                rag_documents = self.user_manager.get_rag_documents(current_user.username)
                if rag_documents:
                    relevant_docs = self.rag_manager.search_similar_documents(query, rag_documents)
                    rag_context = "\n".join([doc['content'] for doc in relevant_docs])
                    response = self.langchain_manager.chat_response(f"Based on the following context:\n{rag_context}\n\nAnswer the query: {query}")
                    self.rag_output.value = response
                else:
                    self.rag_output.value = "No RAG documents found. Please load some documents first."
            else:
                self.rag_output.value = "Please log in to use RAG features."
        else:
            self.rag_output.value = "Please enter a query."

    def setup_ui_components(self):
        # Login components
        self.login_username_input = pn.widgets.TextInput(name="Username", placeholder="Enter username")
        self.login_password_input = pn.widgets.PasswordInput(name="Password", placeholder="Enter password")
        self.login_button = pn.widgets.Button(name="Login", button_type="primary")
        self.login_status_label = pn.widgets.StaticText()
        self.register_link = pn.widgets.Button(name="Not registered? Register here", button_type="primary")
        self.pre_assessment_chat_display = pn.pane.HTML(name="Pre-Assessment Chat Display", sizing_mode='stretch_width')

        

        self.start_practice_button = pn.widgets.Button(name="Start Practice", button_type="primary")
        self.start_mental_state_practice_button = pn.widgets.Button(name="Start Practice on Mental State", button_type="primary")
        self.start_random_practice_button = pn.widgets.Button(name="Start Random Practice", button_type="primary")
    
        self.intro_text = pn.pane.Markdown("""  
    # Welcome to SouLLMate!
    
    SouLLMate is an advanced AI-powered platform tailored specifically for providing comprehensive psychiatric assistance. Designed with a focus on personalized mental health support, our system offers a range of features to cater to individual needs:

    - Personalized Interaction: Engage in real-time, empathetic conversations that understand and adapt to your emotional state.
    - Comprehensive Assessments: Utilize advanced tools to evaluate various aspects of mental health, including stress, anxiety, and depression.
    - Progress Tracking: Monitor your journey with detailed reports and feedback based on interaction and assessment results.
    - Adaptive Learning: Receive suggestions and learning aids that evolve based on your specific mental health needs.
    - Goal Setting: Set personal milestones with customizable plans tailored to improve your mental well-being.
    - Educational Resources: Access a wide array of educational materials to better understand and manage your mental health.
    - Profile Management: Maintain a personal profile that adapts to and grows with your psychiatric journey.
    - Powered by cutting-edge Generative AI tools, SouLLMate aims to provide a sensitive, intelligent, and adaptable psychiatric support system. Each feature is designed to ensure an effective and engaging experience, tested thoroughly to uphold the highest standards of care and assistance.

    Get started today by logging in or registering for an account, and experience a new era of personalized, AI-driven psychiatric support!
    """)
        
        # User manual
        self.user_manual_button = pn.widgets.Button(name="User Manual", button_type="primary")
        self.user_manual_button.on_click(self.show_user_manual)
        self.pdf_viewer = pn.pane.PDF("User_Manual.pdf", width=800, height=600, visible=False)

        # Registration components
        self.reg_username_input = pn.widgets.TextInput(name="Username", placeholder="Enter username")
        self.reg_password_input = pn.widgets.PasswordInput(name="Password", placeholder="Enter password")
        self.reg_nickname_input = pn.widgets.TextInput(name="Nickname", placeholder="Enter your nickname")
        self.reg_email_input = pn.widgets.TextInput(name="Email", placeholder="Enter your email")
        self.register_button = pn.widgets.Button(name="Register", button_type="primary")
        self.reg_status_label = pn.widgets.StaticText()

        # Profile update components
        self.profile_nickname_input = pn.widgets.TextInput(name="Nickname", placeholder="Enter your nickname")
        self.profile_email_input = pn.widgets.TextInput(name="Email", placeholder="Enter your email")
        self.profile_interests_input = pn.widgets.TextAreaInput(name="Interests", placeholder="Enter your interests")
        self.profile_learning_goals_input = pn.widgets.TextAreaInput(name="Learning Goals", placeholder="Enter your learning goals (comma-separated)")
        self.profile_update_button = pn.widgets.Button(name="Update Profile", button_type="primary")
        self.profile_update_status_label = pn.widgets.StaticText()

        # Main interface components
        self.welcome_label = pn.widgets.StaticText(name="SouLLMate")
        self.admin_label = pn.widgets.StaticText(name="Admin Label", visible=False)
        self.logout_button = pn.widgets.Button(name="Logout", button_type="primary")
        
        self.file_input = pn.widgets.FileInput(accept='.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif') 
        self.load_button = pn.widgets.Button(name="Load PDF", button_type="primary")
        
        self.generate_summary_button = pn.widgets.Button(name="Generate Summary", button_type="primary")
        self.generate_question_button = pn.widgets.Button(name="Generate Question", button_type="primary")
        self.submit_answer_button = pn.widgets.Button(name="Submit Answer", button_type="primary")
        self.next_question_button = pn.widgets.Button(name="Next Question", button_type="primary")
        self.finish_exam_button = pn.widgets.Button(name="Finish Exam", button_type="primary")
        self.show_weakness_button = pn.widgets.Button(name="Show Weakness", button_type="primary")
        self.improve_weakness_button = pn.widgets.Button(name="Improve Weakness", button_type="primary")
        
        self.pdf_summary_output = pn.widgets.StaticText(name="PDF Summary")
        self.exam_question_output = pn.widgets.StaticText(name="Exam Question")
        self.exam_answer_input = pn.widgets.TextAreaInput(name="Your Answer", placeholder="Enter your answer", height=200)
        self.exam_status_message = pn.widgets.StaticText(name="Exam Status", value="")
        self.evaluation_result_output = pn.widgets.StaticText(name="Evaluation Result")
        self.weakness_explanation_output = pn.widgets.StaticText(name="Weakness Explanation")
        
        self.chat_display = pn.pane.HTML(name="Chat Display", sizing_mode='stretch_width')
        self.chat_input = pn.widgets.TextAreaInput(name="Chat Input", placeholder="Enter your message", height=100, sizing_mode='stretch_width')
        self.chat_submit_button = pn.widgets.Button(name="Send", button_type="primary")

        # New components for Improve Weakness and Practice
        self.study_material_output = pn.widgets.StaticText(name="Study Material")
        self.generate_more_material_button = pn.widgets.Button(name="Generate More Study Material", button_type="primary")
        self.practice_button = pn.widgets.Button(name="Practice", button_type="primary")
        
        self.practice_topic_input = pn.widgets.TextAreaInput(name="Practice Topic", height=250)
        self.start_practice_button = pn.widgets.Button(name="Start Practice", button_type="primary")
        self.practice_question_output = pn.widgets.StaticText(name="Practice Question")
        self.practice_answer_input = pn.widgets.TextAreaInput(name="Your Answer", height=200, placeholder="Enter your answer here")
        self.submit_practice_answer_button = pn.widgets.Button(name="Submit Answer", button_type="primary")
        self.practice_evaluation_output = pn.widgets.StaticText(name="Evaluation")

        # Learning Plan components
        self.generate_learning_plan_button = pn.widgets.Button(name="Generate Learning Plan", button_type="primary")
        self.learning_plan_output = pn.widgets.StaticText(name="Learning Plan")

        # Notes components
        self.notes_input = pn.widgets.TextAreaInput(name="Notes", placeholder="Enter your notes here", height=300)
        self.save_notes_button = pn.widgets.Button(name="Save Notes", button_type="primary")

        # About Us components
        self.about_us_text = pn.pane.Markdown("""
        # About SouLLMate

        SouLLMate is your personal mental health assistant, designed to provide supportive, adaptive, and insightful conversations tailored to your needs. Our platform combines the latest advancements in artificial intelligence with a deep understanding of psychiatric care to offer real-time support and guidance.

        ## Our Mission
        Our mission is to empower individuals by providing accessible and effective mental health support. We strive to remove barriers to mental health resources, making support available anytime and anywhere.

        ## Development Team:
        - **Qiming Guo** - AI Specialist, Email: [guoqm07@gmail.com](mailto:guoqm07@gmail.com)
        - **Jinwen Tang** - AI/Psychologist Specialist

        We are a team of dedicated professionals, including psychologists, software engineers, and user experience designers, all united by a commitment to enhancing mental health care.
        ## Contact Us
        For support, feedback, or inquiries, please reach out to us at: [support@soullmate.com](mailto:support@soullmate.com).
        We are here to assist you on your journey towards better mental health. Let SouLLMate be a companion you can rely on.

        """)

        # Study Materials components
        self.study_materials_links = pn.pane.Markdown("""
        # Study Materials

        Here are some useful study materials on mental health:

        1. [Understanding Mental Health](https://example.com/understanding-mental-health)
        2. [Common Mental Health Disorders](https://example.com/common-disorders)
        3. [The Impact of Stress on Mental Health](https://example.com/stress-impact)
        4. [Cognitive Behavioral Therapy Essentials](https://example.com/cbt-essentials)
        5. [Mindfulness and Mental Well-being](https://example.com/mindfulness-wellbeing)
        6. [The Role of Nutrition in Mental Health](https://example.com/nutrition-mental-health)
        7. [Mental Health in the Workplace](https://example.com/mental-health-workplace)
        8. [Dealing with Anxiety: Techniques and Tools](https://example.com/dealing-with-anxiety)
        9. [Understanding and Managing Depression](https://example.com/managing-depression)
        10. [Psychotherapy Techniques Overview](https://example.com/psychotherapy-techniques)
        11. [The Science of Happiness](https://example.com/science-happiness)
        12. [Substance Abuse and Mental Health](https://example.com/substance-abuse-mental)
        13. [Mental Health First Aid](https://example.com/mental-health-first-aid)
        14. [Adolescent Mental Health Issues](https://example.com/adolescent-mental-health)
        15. [The Effect of Social Media on Mental Health](https://example.com/social-media-effects)
        16. [Yoga and Mental Health](https://example.com/yoga-mental-health)
        17. [Art Therapy for Mental Health](https://example.com/art-therapy)
        18. [Veterans and Mental Health Care](https://example.com/veterans-mental-health)
        19. [Preventing Mental Health Issues](https://example.com/preventing-mental-health-issues)
        20. [Mental Health and Aging](https://example.com/mental-health-aging)

        More materials will be added regularly. Stay tuned!

        """)

        # Set up button callbacks
        self.login_button.on_click(self.login_user)
        self.register_link.on_click(self.switch_to_register)
        self.register_button.on_click(self.register_user)
        self.logout_button.on_click(self.logout_user)
        self.load_button.on_click(self.load_pdf)
        self.generate_summary_button.on_click(self.generate_summary_callback)
        self.generate_question_button.on_click(self.generate_question_callback)
        self.submit_answer_button.on_click(self.submit_answer_callback)
        self.next_question_button.on_click(self.next_question_callback)
        self.finish_exam_button.on_click(self.finish_exam_callback)
        self.show_weakness_button.on_click(self.show_weakness_callback)
        self.improve_weakness_button.on_click(self.improve_weakness_callback)
        self.back_to_login_button = pn.widgets.Button(name="Back to Login", button_type="primary")
        self.back_to_login_button.on_click(self.switch_to_login)
        self.profile_update_button.on_click(self.update_profile)
        self.practice_button.on_click(self.show_practice_page)
        self.start_practice_button.on_click(self.start_practice)
        self.submit_practice_answer_button.on_click(self.submit_practice_answer)
        self.generate_learning_plan_button.on_click(self.generate_learning_plan)
        self.save_notes_button.on_click(self.save_notes)
        self.generate_more_material_button.on_click(self.generate_more_material)

        self.start_practice_button.on_click(self.start_practice)
        self.start_mental_state_practice_button.on_click(self.start_mental_state_practice)
        self.start_random_practice_button.on_click(self.start_random_practice)



        self.pre_assessment_upload_text = pn.pane.Markdown("1. Upload your personal documents for assessment (diary, social media posts, conversations, story descriptions, etc.). Supports DOCS, PDF, TXT formats.")
        self.pre_assessment_chat_text = pn.pane.Markdown("2. Conduct assessment through dialogue")
        self.pre_assessment_result = pn.widgets.StaticText(name="Assessment Result")
        self.chat_assessment_input = pn.widgets.TextAreaInput(name="Chat Input", placeholder="Share your story or answer AI's questions", height=100)
        self.chat_assessment_button = pn.widgets.Button(name="Send", button_type="primary")
        self.end_assessment_button = pn.widgets.Button(name="End Assessment", button_type="warning")

        self.color_buttons = [
            pn.widgets.Button(name="Azure", button_type="default", width=50, height=30),
            pn.widgets.Button(name="White", button_type="default", width=50, height=30),
            pn.widgets.Button(name="AntiqueWhite", button_type="default", width=50, height=30),
            pn.widgets.Button(name="Beige", button_type="default", width=50, height=30)
        ]


        self.chat_submit_button.on_click(self.on_chat_submit)
        self.chat_assessment_button.on_click(self.on_chat_assessment_submit)
        self.end_assessment_button.on_click(self.end_assessment)

        for button in self.color_buttons:
            button.on_click(self.change_background_color)

        self.bg_image_input = pn.widgets.FileInput(accept='.jpg,.jpeg,.png,.gif')
        self.bg_image_input.param.watch(self.change_background_image, 'value')



    # Color buttons
        # Initialize tabs
        self.tabs = pn.Tabs()

    def show_user_manual(self, event):
        self.pdf_viewer.visible = True
        self.tabs.active = self.tabs.objects.index(self.home_panel)

    def change_background_color(self, event):
        color = event.obj.name.lower()
        js_code = f"""
        <script>
        document.body.style.backgroundColor = '{color}';
        </script>
        """
        self.js_pane.object = js_code


    def create_rag_tab(self):
        return pn.Column(
            pn.Row(pn.pane.Markdown("## RAG (Retrieval-Augmented Generation)")),
            pn.Row(self.rag_folder_input, self.load_rag_folder_button),
            pn.Row(self.rag_file_input, self.load_rag_file_button),
            pn.Row(self.rag_query_input, self.rag_query_button),
            pn.Row(self.rag_output),
            name="RAG"
        )

    def load_rag_from_folder(self, event):
        folder_path = self.rag_folder_input.value
        if folder_path:
            documents = self.load_documents_from_folder(folder_path)
            self.save_rag_documents(documents)
            self.rag_output.value = "Documents loaded successfully from folder."
        else:
            self.rag_output.value = "Please enter a valid folder path."

    def load_rag_file(self, event):
        if self.rag_file_input.value is not None:
            content = self.rag_file_input.value.decode('utf-8')
            filename = self.rag_file_input.filename
            document = {'filename': filename, 'content': content}
            self.save_rag_documents([document])
            self.rag_output.value = "File loaded successfully."
        else:
            self.rag_output.value = "Please select a file to upload."

    def perform_rag_query(self, event):
        query = self.rag_query_input.value
        if query:
            relevant_docs = self.search_similar_documents(query)
            rag_context = "\n".join([doc['content'] for doc in relevant_docs])
            response = self.langchain_manager.chat_response(f"Based on the following context:\n{rag_context}\n\nAnswer the query: {query}")
            self.rag_output.value = response
        else:
            self.rag_output.value = "Please enter a query."

    def load_documents_from_folder(self, folder_path):
        documents = []
        for filename in os.listdir(folder_path):
            if filename.endswith(('.pdf', '.doc', '.docx', '.txt')):
                file_path = os.path.join(folder_path, filename)
                content = self.pdf_processor.load_and_process_pdf(file_path)
                documents.append({'filename': filename, 'content': content})
        return documents

    def save_rag_documents(self, documents):
        current_user = self.user_manager.get_current_user()
        if current_user:
            for doc in documents:
                success, message = self.user_manager.save_rag_document(current_user.username, doc)
                if not success:
                    print(f"Failed to save RAG document: {message}")

    def search_similar_documents(self, query, k=5):
        current_user = self.user_manager.get_current_user()
        if current_user:
            rag_documents = self.user_manager.get_rag_documents(current_user.username)
            if rag_documents:
 
                query_words = set(query.lower().split())
                scored_docs = []
                for doc in rag_documents:
                    doc_words = set(doc['content'].lower().split())
                    similarity = len(query_words.intersection(doc_words)) / len(query_words.union(doc_words))
                    scored_docs.append((similarity, doc))
                scored_docs.sort(reverse=True)
                return [doc for _, doc in scored_docs[:k]]
        return []

    def create_login_tab(self):
        return pn.Column(
            pn.Row(pn.pane.Markdown("## User Login")),
            pn.Row(self.login_username_input, self.login_password_input),
            pn.Row(self.login_button, self.login_status_label),
            pn.Row(self.register_link),
            name="Login"
        )

    def create_learning_tab(self):
        return pn.Column(
            pn.Row(pn.pane.Markdown("## Learning")),
            pn.Row(self.learning_content_output),
            pn.Row(self.continue_learning_button, self.view_history_button),
            name="Learning"
        )
    
    def create_practice_tab(self):
        practice_description = pn.pane.Markdown("""
        Fear comes from the unknown. SouLLMate helps you practice and understand psychological knowledge. 
        Please enter the topic you want to practice, then click Start Practice.
        """, styles={'font-size': '14px', 'color': '#666'})
        
        
        return pn.Column(
            pn.Row(pn.pane.Markdown("## Practice Psych")),
            practice_description,
            pn.Row(self.practice_topic_input),
            pn.Row(self.start_practice_button, self.start_mental_state_practice_button, self.start_random_practice_button),
            pn.Row(self.practice_question_output),
            pn.Row(self.practice_answer_input),
            pn.Row(self.submit_practice_answer_button),
            pn.Row(self.practice_evaluation_output),
            name="Practice Psych"
        )

    def start_mental_state_practice(self, event):
        try:
            current_user = self.user_manager.get_current_user()
            if current_user and current_user.mental_state:
                topic = f"Mental state: {current_user.mental_state}"
                question = self.langchain_manager.generate_practice_question(topic)
                self.practice_question_output.value = question
                self.practice_answer_input.value = ""
                self.practice_evaluation_output.value = ""
                pn.state.notifications.info("Mental state practice question generated")  
            else:
                self.practice_question_output.value = "No mental state information available. Please complete an assessment first."
                pn.state.notifications.warning("No mental state information available")  
        except Exception as e:
            print(f"Error in start_mental_state_practice: {str(e)}")
            self.practice_question_output.value = f"An error occurred: {str(e)}"
            pn.state.notifications.error("Error generating mental state practice question")  


    def start_random_practice(self, event):
        try:
            random_topics = ["cognitive psychology", "developmental psychology", "social psychology", "abnormal psychology", "personality psychology"]
            topic = random.choice(random_topics)
            question = self.langchain_manager.generate_practice_question(topic)
            self.practice_question_output.value = question
            self.practice_answer_input.value = ""
            self.practice_evaluation_output.value = ""
            pn.state.notifications.info(f"Random practice question generated on {topic}") 
        except Exception as e:
            print(f"Error in start_random_practice: {str(e)}")
            self.practice_question_output.value = f"An error occurred: {str(e)}"
            pn.state.notifications.error("Error generating random practice question") 

    def generate_personal_psychology(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user and current_user.mental_state:
            personal_psychology = self.langchain_manager.generate_personal_psychology(current_user.mental_state)
            self.psychology_output.value = personal_psychology
            success, message = self.user_manager.add_study_material(current_user.username, personal_psychology)
            if not success:
                print(f"Failed to save personal psychology: {message}")
        else:
            self.psychology_output.value = "Unable to retrieve user's mental state. Please complete a psychological assessment first."

    def generate_general_psychology(self, event):
        general_psychology = self.langchain_manager.generate_general_psychology()
        self.psychology_output.value = general_psychology
        current_user = self.user_manager.get_current_user()
        if current_user:
            success, message = self.user_manager.add_study_material(current_user.username, general_psychology)
            if not success:
                print(f"Failed to save general psychology: {message}")


    def detect_suicide_risk(self, event):
        chat_history = self.suicide_detection_input.value
        result = self.suicide_detector.process_dataframe(pd.DataFrame({'chat_history': [chat_history]}))
        self.suicide_detection_output.value = str(result['generated_results'].iloc[0])


    def generate_report(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            user_data = self.user_manager.get_user_data(current_user.username)
            report = self.report_generator.generate_report(pd.DataFrame([user_data]))
            

            report_file_path = f"report_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            

            self.report_generator.save_report(report, report_file_path, current_user.username)
            
            self.report_output.value = f"Report saved as {report_file_path}"
            pn.state.notifications.success(f"Report saved as {report_file_path}")
        else:
            pn.state.notifications.error("No user logged in")


    def create_improvement_tab(self):
        return pn.Column(
            pn.Row(pn.pane.Markdown("## Improvement")),
            pn.Row(self.weakness_explanation_output),
            pn.Row(self.study_material_output),
            pn.Row(self.generate_more_material_button, self.practice_button),
            name="Improvement"
        )


    def continue_learning(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            learning_plan = current_user.learning_goals
            current_progress = self.learning_content_output.value
            new_content = self.langchain_manager.generate_learning_content(learning_plan, current_progress)
            self.learning_content_output.value = new_content
            self.user_manager.add_learning_history(current_user.username, new_content)

    def view_learning_history(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            history = self.user_manager.get_learning_history(current_user.username)
            if history:
                history_text = "\n\n".join([f"[{item['timestamp']}]\n{item['content']}" for item in history])
                self.learning_content_output.value = history_text
            else:
                self.learning_content_output.value = "No learning history available."


    def change_background_image(self, event):
        if event.new:
            image_data = base64.b64encode(event.new).decode()
            js_code = f"""
            document.body.style.backgroundImage = 'url(data:image/png;base64,{image_data})';
            document.body.style.backgroundSize = 'cover';
            document.body.style.backgroundRepeat = 'no-repeat';
            document.body.style.backgroundAttachment = 'fixed';
            """
            pn.state.onload(lambda: pn.state.execute(js_code))

    def switch_to_login(self, event=None):
        login_tab = self.create_login_tab()
        self.tabs.clear()
        self.tabs.extend([
            self.home_panel,
            login_tab
        ])

    def create_dashboard(self):
        pn.extension(template='fast', theme=None)
        pn.state.background = 'white'  

        self.home_panel = pn.Column(
            self.intro_text,
            pn.layout.Divider(),
            pn.Row(self.user_manual_button),
            self.pdf_viewer,
            sizing_mode='stretch_width',
            name="Home"
        )
        
        login_tab = self.create_login_tab()
        
        self.tabs.clear()
        self.tabs.extend([
            self.home_panel,
            login_tab
        ])
        
       
        bottom_row = pn.Row(*self.color_buttons)

        dashboard = pn.Column(
            self.tabs,
            bottom_row,
            self.js_pane,
            sizing_mode='stretch_width'
        )
        return dashboard

    def create_register_tab(self):
        return pn.Column(
            pn.Row(pn.pane.Markdown("## User Registration")),
            pn.Row(self.reg_username_input, self.reg_password_input),
            pn.Row(self.reg_nickname_input, self.reg_email_input),
            pn.Row(self.register_button, self.reg_status_label),
            pn.Row(self.back_to_login_button),
            name="Register"
        )


    def create_profile_update_tab(self):
        current_user = self.user_manager.get_current_user()
        if current_user:
            current_info = pn.pane.Markdown(f"""
            ## Current Profile Information
            Username: {current_user.username}
            Nickname: {current_user.nickname or 'Not set'}
            Email: {current_user.email or 'Not set'}
            Interests: {current_user.interests or 'Not set'}
            """)
        else:
            current_info = pn.pane.Markdown("Error: No user logged in.")

        self.profile_nickname_input.value = current_user.nickname if current_user else ""
        self.profile_email_input.value = current_user.email if current_user else ""
        self.profile_interests_input.value = current_user.interests if current_user else ""
        self.profile_mental_state_input.value = ""  

        return pn.Column(
            current_info,
            pn.layout.Divider(),
            pn.Row(pn.pane.Markdown("## Update Profile")),
            pn.Row(self.profile_nickname_input, self.profile_email_input),
            pn.Row(self.profile_interests_input),
            pn.Row(self.profile_mental_state_input),
            pn.Row(self.profile_update_button, self.profile_update_status_label),
            name="Profile"
        )

    def create_history_tab(self):
        current_user = self.user_manager.get_current_user()
        if current_user:

            session = self.user_manager.Session()
            current_user = session.query(User).get(current_user.id)
            session.refresh(current_user)
            session.close()

            print(f"Current user: {current_user.username}")
            print(f"Exam history: {current_user.exam_history}")

            exam_count = len(current_user.exam_history) if current_user.exam_history else 0
            stats = pn.pane.Markdown(f"""
            ## User Statistics
            Username: {current_user.username}
            Number of evaluations: {exam_count}
            """)

            history_items = []
            if current_user.exam_history:
                for exam in current_user.exam_history:
                    history_items.append(pn.pane.Markdown(f"""
                    **Date:** {exam['date']}
                    
                    **Question:** 
                    {exam['question']}
                    
                    **Answer:** 
                    {exam['answer']}
                    
                    **Evaluation:** 
                    {exam['evaluation']}
                    
                    ---
                    """))
            else:
                history_items.append(pn.pane.Markdown("No evaluation history available."))

            return pn.Column(
                stats,
                pn.layout.Divider(),
                pn.pane.Markdown("## Evaluation History"),
                *history_items,
                name="History"
            )
        else:
            return pn.Column(pn.pane.Markdown("Please log in to view your history."), name="History")

    def create_logged_in_tabs(self):

        profile_update_tab = self.create_profile_update_tab()

        rag_tab = self.create_rag_tab()

        welcome_tab = pn.Column(
            pn.Row(self.welcome_label),
            pn.Row(self.admin_label),
            pn.Row(self.logout_button),  
            pn.Row(pn.pane.Markdown("## Chat with SouLLMate")),
            pn.Row(self.chat_display),
            pn.Row(self.chat_input, self.chat_submit_button),
            name="Interactive Chat and Advisory"
        )
        
        pre_assessment_tab = pn.Column(
            pn.Row(pn.pane.Markdown("## Pre-Assessment")),
            pn.Row(self.pre_assessment_upload_text),
            pn.Row(self.file_input, self.load_button),
            pn.Row(self.pre_assessment_chat_text),
            pn.Row(self.pre_assessment_chat_display),
            pn.Row(self.chat_assessment_input, self.chat_assessment_button),
            pn.Row(self.end_assessment_button),
            pn.Row(self.pre_assessment_result),
            name="Pre-Assessment"
        )

        suicide_detection_tab = pn.Column(
            pn.Row(pn.pane.Markdown("## Suicide Risk Detection")),
            pn.Row(self.suicide_detection_input),
            pn.Row(self.suicide_detection_button),
            pn.Row(self.suicide_detection_output),
            name="Suicide Detection"
        )

        report_tab = pn.Column(
            pn.Row(pn.pane.Markdown("## Report Generation")),
            pn.Row(self.generate_report_button),
            pn.Row(self.report_output),
            name="Report"
        )

        exam_tab = pn.Column(
            pn.Row(self.file_input, self.load_button),
            pn.Row(self.generate_summary_button, pn.pane.Markdown("## PDF Summary", sizing_mode='stretch_width')),
            pn.Row(pn.Column(self.pdf_summary_output, height=200, width=800, scroll=True)),
            pn.Row(self.generate_question_button, self.exam_question_output),
            pn.Row(self.exam_answer_input, self.submit_answer_button),
            pn.Row(self.next_question_button, self.finish_exam_button),
            pn.Row(self.exam_status_message), 
            name="Exam"
        )


        psychology_tab = pn.Column(
            pn.Row(pn.pane.Markdown("## Learn Psychology")),
            pn.Row(self.understand_self_button, self.understand_general_psych_button),
            pn.Row(self.psychology_output),
            name="Learn Psychology"
        )

        exam_evaluation_tab = pn.Column(
            pn.Row(pn.pane.Markdown("## Exam Evaluation")),
            pn.Row(self.evaluation_result_output),
            pn.Row(self.show_weakness_button, self.improve_weakness_button),
            name="Exam Evaluation"
        )

        improvement_tab = pn.Column(
            pn.Row(pn.pane.Markdown("## Improvement")),
            pn.Row(self.weakness_explanation_output),
            pn.Row(self.study_material_output),
            pn.Row(self.generate_more_material_button, self.practice_button),
            name="Improvement"
        )

        practice_tab = pn.Column(
            pn.Row(pn.pane.Markdown("## Practice Psych")),
            pn.Row(self.practice_topic_input),
            pn.Row(self.start_practice_button, self.start_mental_state_practice_button, self.start_random_practice_button),
            pn.Row(self.practice_question_output),
            pn.Row(self.practice_answer_input),
            pn.Row(self.submit_practice_answer_button),
            pn.Row(self.practice_evaluation_output),
            name="Practice Psych"
        )

        learning_plan_tab = pn.Column(
            pn.Row(pn.pane.Markdown("## Learning Plan")),
            pn.Row(self.generate_learning_plan_button),
            pn.Row(self.learning_plan_output),
            name="Learning Plan"
        )

        notes_tab = pn.Column(
            pn.Row(pn.pane.Markdown("## Notes")),
            pn.Row(self.notes_input),
            pn.Row(self.save_notes_button),
            name="Notes"
        )

        about_us_tab = pn.Column(
            self.about_us_text,
            name="About Us"
        )

        study_materials_tab = pn.Column(
            self.study_materials_links,
            name="Study Materials"
        )

        # learning_tab = self.create_learning_tab()
    
        history_tab = ("History", self.create_history_tab())

        intervention_tab = self.create_intervention_tab()
        
        self.tabs.clear()
        self.tabs.extend([
            profile_update_tab, 
            welcome_tab, 
            intervention_tab,
            pre_assessment_tab,
            suicide_detection_tab,
            report_tab,
            psychology_tab, 
            notes_tab, 
            rag_tab,
            study_materials_tab,
            about_us_tab
        ])
        self.intervention_chat_button.on_click(self.on_intervention_chat_submit)

    def login_user(self, event):
        username = self.login_username_input.value
        password = self.login_password_input.value
        success, message = self.user_manager.login_user(username, password)
        if success:
            self.login_status_label.value = ""
            current_user = self.user_manager.get_current_user()
            if current_user:
                self.welcome_label.value = f"Welcome, {current_user.nickname or current_user.username}! \n Within every breath of life, there lies hope. Remember, no matter how fierce the storm may be, there is always a rainbow after the rain. Here at SouLLMate, we are committed to walking with you through the storms, offering support, guidance, and resources to help you find your rainbow. Let's start this journey together!"
                self.admin_label.visible = current_user.role == "admin"
                self.create_logged_in_tabs()
                self.load_user_notes()
                self.refresh_history_tab()  
                self.tabs.active = 0  
            else:
                self.login_status_label.value = "Error retrieving user data."
        else:
            self.login_status_label.value = message

    def switch_to_register(self, event):
        register_tab = self.create_register_tab()
        self.tabs.clear()
        self.tabs.extend([
            self.home_panel,
            register_tab
        ])

    def register_user(self, event):
        username = self.reg_username_input.value
        password = self.reg_password_input.value
        nickname = self.reg_nickname_input.value
        email = self.reg_email_input.value
        success, message = self.user_manager.register_user(username, password, nickname, email)
        if success:
            self.reg_status_label.value = "Registration successful. Please log in."
            self.switch_to_login()
        else:
            self.reg_status_label.value = f"Registration failed: {message}"

    def logout_user(self, event):
        success, message = self.user_manager.logout_user()
        if success:
            self.welcome_label.value = "Welcome to Smart Tutor System!"
            self.admin_label.visible = False
            self.switch_to_login()

    def load_pdf(self, event):
        if self.file_input.value is not None:
            file_extension = os.path.splitext(self.file_input.filename)[1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(self.file_input.value)
                temp_file_path = temp_file.name

            self.page_content = self.pdf_processor.load_and_process_pdf(temp_file_path)
            self.load_button.name = "File Loaded"
            self.load_button.button_type = "success"
            
            assessment_prompt = f"""You are an AI assistant tasked with simulating a mental health assessment based on the provided text. This is not a real clinical diagnosis, but a demonstration of how such an assessment might be structured. Using the information given, create a hypothetical assessment of the individual's mental health over the last two weeks using an 8-question survey. The survey evaluates:

            1. Lack of interest in activities
            2. Feelings of depression or hopelessness
            3. Sleep issues
            4. Low energy
            5. Changes in appetite
            6. Negative self-perception
            7. Concentration difficulties
            8. Unusual movement or speech patterns

            For each question, assign a hypothetical score from 0 (Not at all) to 3 (Nearly every day) based on the information provided in the text. Sum up these scores for a total ranging from 0 to 24.

            Your response MUST follow this exact format, with each section separated by a newline:
            
            1. Total score: X (where X is the calculated score between 0 and 24)

            2. Individual scores:

                1. Lack of interest in activities: [score];

                2. Feelings of depression or hopelessness: [score];

                3. Sleep issues: [score];

                4. Low energy: [score];

                5. Changes in appetite: [score];

                6. Negative self-perception: [score];

                7. Concentration difficulties: [score];

                8. Unusual movement or speech patterns: [score];

            3. Explanation: A brief explanation of your reasoning for these scores in under 600 tokens.

            Your entire response, including the total score, individual scores, and explanation, must not exceed 2048 tokens.

            Here is the text to analyze:
            {self.page_content}

            Remember, this is a simulated assessment for demonstration purposes only. It's crucial to provide the total score as specified and keep your explanation concise."""
            
            assessment_result = self.langchain_manager.chat_response(assessment_prompt)
            self.pre_assessment_result.value = assessment_result

            # Update user's mental state
            current_user = self.user_manager.get_current_user()
            if current_user:
                success, message = self.user_manager.update_mental_state(current_user.username, assessment_result)
                if success:
                    self.refresh_user_profile()
                else:
                    print(f"Failed to update mental state: {message}")

            os.unlink(temp_file_path)

    def generate_summary_callback(self, event):
        self.pdf_summary = self.langchain_manager.generate_summary(self.page_content)
        self.pdf_summary_output.value = self.pdf_summary
        self.exam_question_output.value = ""
        self.exam_answer_input.value = ""
        self.generate_question_button.disabled = False

    def generate_question_callback(self, event):
        if self.pdf_summary_output.value:
            self.pdf_exam_question = self.langchain_manager.generate_exam_question(self.pdf_summary_output.value)
            self.exam_question_output.value = self.pdf_exam_question.replace('\n', '<br>')
            self.exam_answer_input.value = ""
            self.submit_answer_button.disabled = False
        else:
            self.exam_question_output.value = "Please generate a summary first."

    def submit_answer_callback(self, event):
        if self.exam_question_output.value and self.exam_answer_input.value:
            current_user = self.user_manager.get_current_user()
            if current_user:
                if current_user.questions is None:
                    current_user.questions = []
                if current_user.answers is None:
                    current_user.answers = []
                current_user.questions.append(self.exam_question_output.value)
                current_user.answers.append(self.exam_answer_input.value)
                self.user_manager.save_user_data(current_user.username, current_user.to_dict())
            self.exam_answer_input.value = ""
            self.next_question_button.disabled = False
            self.finish_exam_button.disabled = False
        else:
            self.exam_question_output.value = "Please generate a question and provide an answer."

    def next_question_callback(self, event):
        self.exam_question_output.value = ""
        self.generate_question_button.disabled = False
        self.submit_answer_button.disabled = True
        self.next_question_button.disabled = True

    def finish_exam_callback(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            user_data = current_user.to_dict()
            evaluations = []
            weaknesses = []

            self.exam_status_message.value = "Generating exam evaluations..."

            for question, answer in zip(user_data['questions'], user_data['answers']):
                evaluation = self.langchain_manager.evaluate_student_answer(user_data['nickname'] or user_data['username'], question, answer)
                evaluations.append(evaluation)
                weakness = self.langchain_manager.generate_weakness_explanation(evaluation)
                weaknesses.append(weakness)
                self.exam_status_message.value = f"Generated evaluation for question {len(evaluations)}"

            self.exam_status_message.value = "Saving exam results..."

            exam_data = {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'question': '\n'.join(user_data['questions']),
                'answer': '\n'.join(user_data['answers']),
                'evaluation': '\n\n'.join(evaluations)
            }

            user_data['evaluations'] = evaluations
            user_data['weaknesses'] = weaknesses

            success = self.user_manager.save_user_data(current_user.username, user_data)
            print(f"User data saved: {success}")

            success, message = self.user_manager.add_exam_history(current_user.username, exam_data)
            if not success:
                print(f"Failed to save exam history: {message}")

            user_data['questions'] = []
            user_data['answers'] = []

            print(f"Evaluations: {evaluations}")
            print(f"Weaknesses: {weaknesses}")

            self.evaluation_result_output.value = "\n\n".join(evaluations)
            self.tabs.active = self.tabs.objects.index(next(tab for tab in self.tabs if tab.name == "Exam Evaluation"))

            self.exam_question_output.value = ""
            self.exam_answer_input.value = ""
            self.exam_status_message = pn.widgets.StaticText(name="Exam Status", value="")
            self.generate_question_button.disabled = False
            self.submit_answer_button.disabled = True
            self.next_question_button.disabled = True
            self.finish_exam_button.disabled = True
        else:
            self.evaluation_result_output.value = "Error: No user logged in."

    def show_weakness_callback(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            user_data = self.user_manager.get_user_data(current_user.username)
            if user_data and 'weaknesses' in user_data and user_data['weaknesses']:
                weakness = user_data['weaknesses'][-1]
                print(f"Selected weakness: {weakness}")
                self.weakness_explanation_output.value = weakness
                study_material = self.langchain_manager.generate_study_material(weakness)
                self.study_material_output.value = study_material
                self.tabs.active = self.tabs.objects.index(next(tab for tab in self.tabs if tab.name == "Improvement"))
        else:
            self.weakness_explanation_output.value = "No weaknesses identified yet."

    def improve_weakness_callback(self, event):
        self.tabs.active = 3  # Switch to Improve Weakness tab

    def on_chat_submit(self, event):
        user_input = self.chat_input.value
        self.chat_input.value = ""

        if user_input:
            full_prompt = self.predefined_prompt + user_input
            response = self.langchain_manager.chat_response(full_prompt)
            if response:
                self.update_chat_display(user_input, response)
            else:
                self.update_chat_display(user_input, "I apologize, but I couldn't generate a response. Please try again.")


    def on_chat_assessment_submit(self, event):
        user_input = self.chat_assessment_input.value
        self.chat_assessment_input.value = ""

        if user_input:
            if not hasattr(self, 'assessment_conversation_history'):
                self.assessment_conversation_history = []
            self.assessment_conversation_history.append(f"User: {user_input}")

            full_prompt = self.chat_assessment_prompt.format(
                conversation_history="\n".join(self.assessment_conversation_history)
            )
            response = self.langchain_manager.chat_response(full_prompt)
            
            if response:
                self.assessment_conversation_history.append(f"AI: {response}")
                self.update_pre_assessment_chat_display(user_input, response)
            else:
                self.update_pre_assessment_chat_display(user_input, "I apologize, but I couldn't generate a response. Please try again.")

    def update_pre_assessment_chat_display(self, user_input, ai_response):
        current_content = self.pre_assessment_chat_display.object if self.pre_assessment_chat_display.object else ""
        new_content = f"{current_content}<p><strong>You:</strong> {user_input}</p><p><strong>SouLLMate:</strong> <span style='color: #4a86e8;'>{ai_response}</span></p>"
        self.pre_assessment_chat_display.object = new_content
        if hasattr(pn.state, 'notifications') and pn.state.notifications is not None:
            pn.state.notifications.info("Chat updated")
        else:
            print("Chat updated")  


    def end_assessment(self, event):
        if hasattr(self, 'assessment_conversation_history') or self.page_content:
            interview_content = "\n".join(self.assessment_conversation_history) if hasattr(self, 'assessment_conversation_history') else self.page_content
            
            assessment_prompt = f"""You are an AI assistant tasked with simulating a mental health assessment based on the provided text. This is not a real clinical diagnosis, but a demonstration of how such an assessment might be structured. Using the information given, create a hypothetical assessment of the individual's mental health over the last two weeks using an 8-question survey. The survey evaluates:

            1. Lack of interest in activities
            2. Feelings of depression or hopelessness
            3. Sleep issues
            4. Low energy
            5. Changes in appetite
            6. Negative self-perception
            7. Concentration difficulties
            8. Unusual movement or speech patterns

            For each question, assign a hypothetical score from 0 (Not at all) to 3 (Nearly every day) based on the information provided in the text. Sum up these scores for a total ranging from 0 to 24.

            Your response MUST follow this exact format, with each section separated by a newline:
            
            1. Total score: X (where X is the calculated score between 0 and 24)

            2. Individual scores:

                1. Lack of interest in activities: [score];

                2. Feelings of depression or hopelessness: [score];

                3. Sleep issues: [score];

                4. Low energy: [score];

                5. Changes in appetite: [score];

                6. Negative self-perception: [score];

                7. Concentration difficulties: [score];

                8. Unusual movement or speech patterns: [score];

            3. Explanation: A brief explanation of your reasoning for these scores in under 600 tokens.

            Your entire response, including the total score, individual scores, and explanation, must not exceed 2048 tokens.

            Here is the text to analyze:
            {interview_content}

            Remember, this is a simulated assessment for demonstration purposes only. It's crucial to provide the total score as specified and keep your explanation concise."""



            assessment_result = self.langchain_manager.chat_response(assessment_prompt)
            self.pre_assessment_result.value = assessment_result

            # Update user's mental state
            current_user = self.user_manager.get_current_user()
            if current_user:
                success, message = self.user_manager.update_mental_state(current_user.username, assessment_result)
                if success:
                    self.refresh_user_profile()
                else:
                    print(f"Failed to update mental state: {message}")

            # Clear conversation history and page content
            if hasattr(self, 'assessment_conversation_history'):
                del self.assessment_conversation_history
            self.page_content = ""
            self.pre_assessment_chat_display.object = ""
        else:
            self.pre_assessment_result.value = "No assessment data available."

    def create_intervention_tab(self):

        self.intervention_chat_button.on_click(self.on_intervention_chat_submit)
        return pn.Column(
            pn.Row(pn.pane.Markdown("## Intervention Chat")),
            pn.Row(self.intervention_chat_display),
            pn.Row(self.intervention_chat_input, self.intervention_chat_button),
            name="Intervention"
        )
    

    def on_intervention_chat_submit(self, event):
        user_input = self.intervention_chat_input.value
        self.intervention_chat_input.value = ""
        
        if user_input:
            current_user = self.user_manager.get_current_user()
            if current_user and current_user.mental_state:
                full_prompt = f"Given the user's mental state: {current_user.mental_state}\n\nUser input: {user_input}\n\nProvide a supportive and guiding response:"
                response = self.langchain_manager.chat_response(full_prompt)
                if response:
                    self.update_intervention_chat_display(user_input, response)
                    intervention_data = {
                        'user_input': user_input,
                        'response': response,
                        'timestamp': datetime.now().isoformat()
                    }
                    success, message = self.user_manager.add_intervention_history(current_user.username, intervention_data)
                    if not success:
                        print(f"Failed to save intervention history: {message}")
                else:
                    self.update_intervention_chat_display(user_input, "I apologize, but I couldn't generate a response. Please try again.")
            else:
                self.update_intervention_chat_display(user_input, "No mental state assessment available. Please complete an assessment first.")

    def update_intervention_chat_display(self, user_input, ai_response):
        current_content = self.intervention_chat_display.object if self.intervention_chat_display.object else ""
        new_content = f"{current_content}<p><strong>You:</strong> {user_input}</p><p><strong>SouLLMate:</strong> <span style='color: #4a86e8;'>{ai_response}</span></p>"
        self.intervention_chat_display.object = new_content

    def update_chat_display(self, user_input, ai_response):
        current_content = self.chat_display.object if self.chat_display.object else ""
        new_content = f"{current_content}<p><strong>You:</strong> {user_input}</p><p><strong>SouLLMate:</strong> <span style='color: #4a86e8;'>{ai_response}</span></p>"
        self.chat_display.object = new_content

    def update_profile(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            nickname = self.profile_nickname_input.value
            email = self.profile_email_input.value
            interests = self.profile_interests_input.value
            mental_state = self.profile_mental_state_input.value
            
            success, message = self.user_manager.update_user_profile(
                current_user.username, nickname, email, interests, mental_state
            )
            
            if success:
                self.profile_update_status_label.value = "Profile updated successfully."
                self.welcome_label.value = f"Welcome, {nickname or current_user.username}!"
                self.refresh_user_profile()
            else:
                self.profile_update_status_label.value = f"Profile update failed: {message}"
        else:
            self.profile_update_status_label.value = "Error: No user logged in."


    def refresh_psychology_tab(self):
            psychology_tab = next((tab for tab in self.tabs if tab.name == "Learn Psychology"), None)
            if psychology_tab:
                new_psychology_content = pn.Column(
                    pn.Row(pn.pane.Markdown("## Learn Psychology")),
                    pn.Row(self.understand_self_button, self.understand_general_psych_button),
                    pn.Row(self.psychology_output),
                    name="Learn Psychology"
                )
                index = next(i for i, tab in enumerate(self.tabs) if tab.name == "Learn Psychology")
                self.tabs[index] = (psychology_tab.name, new_psychology_content)

    def refresh_user_profile(self):
        current_user = self.user_manager.get_current_user()
        if current_user:
            profile_tab = next((tab for tab in self.tabs if tab.name == "Profile"), None)
            if profile_tab:
                new_profile_content = self.create_profile_update_tab()
                index = next(i for i, tab in enumerate(self.tabs) if tab.name == "Profile")
                self.tabs[index] = (profile_tab.name, new_profile_content)
            
            self.refresh_history_tab()
            self.refresh_psychology_tab()
            self.refresh_learning_plan_tab()

    def refresh_history_tab(self):
        history_tab = next((tab for tab in self.tabs if tab.name == "History"), None)
        if history_tab:
            new_history_content = self.create_history_tab()
            index = next(i for i, tab in enumerate(self.tabs) if tab.name == "History")
            self.tabs[index] = (history_tab.name, new_history_content)

    def refresh_learning_plan_tab(self):
        learning_plan_tab = next((tab for tab in self.tabs if tab.name == "Learning Plan"), None)
        if learning_plan_tab:
            current_user = self.user_manager.get_current_user()
            if current_user:
                user_data = self.user_manager.get_user_data(current_user.username)
                learning_goals = ', '.join(user_data['learning_goals']) if user_data['learning_goals'] else 'No learning goals set'
                self.learning_plan_output.value = f"Current Learning Goals:\n{learning_goals}"

    def generate_more_material(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            current_weakness = self.weakness_explanation_output.value
            more_material = self.langchain_manager.generate_study_material(current_weakness)
            self.study_material_output.value += "\n\n" + more_material
            
            success, message = self.user_manager.add_study_material(current_user.username, more_material)
            if not success:
                print(f"Failed to save study material: {message}")

    def show_practice_page(self, event):
        self.practice_topic_input.value = self.weakness_explanation_output.value
        self.tabs.active = 4  # Switch to Practice tab


    def start_practice(self, event):
        print("start_practice function called")
        try:
            topic = self.practice_topic_input.value
            if topic.strip():
                print(f"Generating question for topic: {topic}")
                question = self.langchain_manager.generate_practice_question(topic)
                print(f"Generated question: {question}")
                self.practice_question_output.value = question
                self.practice_answer_input.value = ""
                self.practice_evaluation_output.value = ""
                pn.state.notifications.info("Practice question generated")
            else:
                print("No topic provided")
                self.practice_question_output.value = "Please enter a topic before starting practice."
                pn.state.notifications.warning("No topic provided")
            print("Practice started successfully")
        except Exception as e:
            print(f"Error in start_practice: {str(e)}")
            self.practice_question_output.value = f"An error occurred: {str(e)}"
            pn.state.notifications.error("Error generating practice question") 

    def submit_practice_answer(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            question = self.practice_question_output.value
            answer = self.practice_answer_input.value
            evaluation = self.langchain_manager.evaluate_practice_answer(question, answer)
            self.practice_evaluation_output.value = evaluation
            

            practice_data = {
                'question': question,
                'answer': answer,
                'evaluation': evaluation,
                'timestamp': datetime.now().isoformat()
            }
            success, message = self.user_manager.add_practice_history(current_user.username, practice_data)
            if not success:
                print(f"Failed to save practice history: {message}")

    def generate_learning_plan(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            user_data = current_user.to_dict()
            learning_plan = self.langchain_manager.generate_learning_plan(user_data)
            self.learning_plan_output.value = learning_plan
            

            learning_goals = learning_plan.split('\n')[:5]  
            success, message = self.user_manager.update_user_profile(
                current_user.username, 
                current_user.nickname, 
                current_user.email, 
                current_user.interests, 
                learning_goals
            )
            if success:
                self.refresh_user_profile()  
            else:
                print(f"Failed to update learning goals: {message}")

    def save_notes(self, event):
        current_user = self.user_manager.get_current_user()
        if current_user:
            notes = self.notes_input.value
            success, message = self.user_manager.save_user_notes(current_user.username, notes)
            if success:
                pn.state.notifications.success("Notes saved successfully.")
            else:
                pn.state.notifications.error(f"Failed to save notes: {message}")

    def load_user_notes(self):
        current_user = self.user_manager.get_current_user()
        if current_user:
            notes = self.user_manager.get_user_notes(current_user.username)
            if notes:
                self.notes_input.value = notes

class App:
    def __init__(self):
        self.config = Config()
        self.rag_folder = "Rag_document"
        if not os.path.exists(self.rag_folder):
            os.makedirs(self.rag_folder)
        self.rag_manager = RAGManager(self.rag_folder)
        self.user_manager = UserManager()
        self.pdf_processor = PDFProcessor()
        self.langchain_manager = LangchainManager()
        self.suicide_detector = SuicideDetector()
        self.report_generator = ReportGenerator()
        self.ui_manager = UIManager(self.user_manager, self.pdf_processor, self.langchain_manager, self.suicide_detector, self.report_generator, self.rag_manager)

    def run(self):
        pn.extension(design='material')
        template = pn.template.MaterialTemplate(title="SouLLMate - Your Personal Psychiatrist Assistant")
        dashboard = self.ui_manager.create_dashboard()
        template.main.append(dashboard)
        pn.serve(template, show=True, port=5006)

if __name__ == "__main__":
    app = App()
    app.run()