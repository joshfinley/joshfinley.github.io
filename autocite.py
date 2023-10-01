import os
import re
from langchain.document_loaders import PyPDFLoader
from langchain.llms import OpenAI

# Initialize the LLM (Language Model)
llm = OpenAI(temperature=0.9)

# Function to generate citation based on file content
def generate_citation(file_path, file_type):
    data = ""
    if file_type == ".pdf":
        loader = PyPDFLoader(file_path)
        data = loader.load()
    else:
        return

    first_page = data[0]
    citation = llm(f"""
Write an APA citation based on the first page of this document. 
If its difficult to read the document, check if the document
title is very familiar to your training data and whether you 
already know the authors, publish date, etc.
                   
{first_page}
""")
    return citation

def replace_citation_in_post(post_path, ref, citation):
    with open(post_path, 'r') as f:
        post_content = f.read()

    reference_shortcode_pattern = '{{< reference content="{}" citation="([^"]*)" >}}'.format(ref)

    match = re.search(reference_shortcode_pattern, post_content)
    if match and match.group(1):
        print(f"Citation already present in: {post_path}")
        return

    new_shortcode = '{{< reference content="{}" citation="{}" >}}'.format(ref, citation)
    post_content = re.sub(reference_shortcode_pattern, new_shortcode, post_content)

    with open(post_path, 'w') as f:
        f.write(post_content)
    
    print(f"Added citation to: {post_path} [{citation}] ")

for post in os.listdir("content/posts"):
    if post.endswith(".md"):
        post_path = os.path.join("content/posts", post)

        with open(post_path, "r") as f:
            post_content = f.read()

        references = re.findall(r'{{< reference content="([^"]+)"', post_content, re.IGNORECASE)

        for ref in references:
            filename, extension = os.path.splitext(ref)
            
            if extension != ".pdf":
                continue

            full_ref_path = "static" + ref

            if os.path.exists(full_ref_path):
                citation = generate_citation(full_ref_path, extension).strip('\n')
                replace_citation_in_post(post_path, ref, citation)
            else:
                print(f"File {full_ref_path} not found.")
