import getpass
import os
import json
from langchain_openrouter import ChatOpenRouter
from langchain_community.document_loaders import PyPDFLoader

#do i put in my api key in this
if not os.getenv("OPENROUTER_API_KEY"):
    os.environ["OPENROUTER_API_KEY"] = getpass.getpass("Enter your OpenRouter API key: ")
    
"""
#enable model tracing from langchain dont know if i need it 
os.environ["LANGSMITH_API_KEY"] = getpass.getpass("Enter your LangSmith API key: ")
os.environ["LANGSMITH_TRACING"] = "true" """

model = ChatOpenRouter(model="nvidia/nemotron-3.5-lightning:free",temperature=0)

#for the pdfs 
prompt= """ You are a academic assigment planning agent. You read the uploaded pdfs for the assignment and analyse the assignement brief
Extract:
1. Assignment title and module, if available.
2. Submission deadline, including time and timezone if stated.
3. Deliverables.
4. Marking criteria and their weightings.
5. A breakdown into actionable subtasks.
6. Estimated effort in hours for each subtask.
7. Milestones that should be completed before the deadline.
8. Task type (essay, poster, ppt etc)
Only report the facts supported by the assignment brief. Never invent a deadline, word count or weight if it is not explicitly said. distinguish requirements 
from your own suggestions. 

Return valid JSON using this structure:
{
    "title": "",
    "module": "",
    "task_type": "",
    "subject": "",
    "due": "",
    "estimated_minutes": "",
    "weightage": ""
}
"""

def retrieve_pdf(pdf_path):
    """Retrieve relevant information"""
    loader= PyPDFLoader(pdf_path)
    documents= loader.load()
    return "\n".join(doc.page_content for doc in documents)

def output(pdf_path):
    assignment_text= retrieve_pdf(pdf_path)

    response = model.invoke([("system", prompt),
        (
            "human",
            "Analyse this assignment brief:\n\n"
            + assignment_text
        )
    ])

    #convert the response into a Python dictionary
    result = json.loads(response.content)
    return result
if __name__=="__main__":
    pdf_path = input("Enter the path to your assignment PDF: ")
    assignment = output(pdf_path)
    print(json.dumps(assignment, indent=4))

