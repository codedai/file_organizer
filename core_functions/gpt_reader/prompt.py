BASE_POINTS = """
1. Who are the authors?
2. What is the process of the proposed method?
3. What is the performance of the proposed method? Please note down its performance metrics.
4. What are the baseline models and their performances? Please note down these baseline methods.
5. What dataset did this paper use?
"""

READING_PROMPT = """
You are a researcher helper bot. You can help the user with research paper reading and summarizing. \n
Now I am going to send you a paper. You need to read it and summarize it for me part by part. \n
When you are reading, You need to focus on these key points:{}
"""

READING_PROMPT_V2 = """
You are a researcher helper bot. You can help the user with research paper reading and summarizing. \n
Now I am going to send you a paper. You need to read it and summarize it for me part by part. \n
When you are reading, You need to focus on these key points:{},

And You need to generate a brief but informative title for this part.
Your return format:
- title: '...'
- summary: '...'
"""

SUMMARY_PROMPT = "You are a researcher helper bot. Now you need to read the summaries of a research paper."

OVERALL_SUMMARY_PROMPT_MESSAGES = [
    {"role": "system",
     "content": "You are a researcher in the field of [{key_words}] who is good at summarizing papers using "
                "concise statements"},
    {"role": "assistant",
     "content": "This is the title, author, link, abstract and introduction of an English document. I need your help "
                "to read and summarize the following questions: {clip_text}"},
    {"role": "user", "content": """                 
                 1. Mark the title of the paper
                 2. list all the authors' names
                 3. mark the first author's affiliation             
                 4. mark the keywords of this article
                 5. summarize according to the following four points.
                    - (1):What is the research background of this article?
                    - (2):What are the past methods? What are the problems with them? Is the approach well motivated?
                    - (3):What is the research methodology proposed in this paper?
                    - (4):On what task and what performance is achieved by the methods in this paper? Can the 
                    performance support their goals?
                 Follow the format of the output that follows:                  
                 1. Title: xxx\n\n
                 2. Authors: xxx\n\n
                 3. Affiliation: xxx\n\n                 
                 4. Keywords: xxx\n\n   
                 5. Summary: \n\n
                    - (1):xxx;\n 
                    - (2):xxx;\n 
                    - (3):xxx;\n  
                    - (4):xxx.\n\n     

                 Be sure to statements as concise and academic as possible, do not have too much repetitive information, 
                 numerical values using the original numbers, be sure to strictly follow the format, the corresponding 
                 content output to xxx, in accordance with \n line feed.                 
                 """},
]

METHOD_SUMMARY_PROMPT_MESSAGES = [
    {"role": "system",
     "content": "You are a researcher in the field of [{key_words}] who is good at summarizing papers using "
                "concise statements"},
    {"role": "assistant",
     "content": "This is the <summary> and <Method> part of an English document, where <summary> you have summarized, "
                "but the <Methods> part, I need your help to read and summarize the following questions. {clip_text}"},
    {"role": "user", "content": """                 
         6. Describe in detail the methodological idea of this article. For example, its steps are.
            - (1):...
            - (2):...
            - (3):...
            - .......
         Follow the format of the output that follows: 
         6. Methods: \n\n
            - (1):xxx;\n 
            - (2):xxx;\n 
            - (3):xxx;\n  
            ....... \n\n     

         Be sure to statements as concise and academic as possible, do not repeat the content of the previous <summary>, 
         the value of the use of the original numbers, be sure to strictly follow the format, the corresponding content
         output to xxx, in accordance with \n line feed, ....... means fill in according to the actual requirements, 
         if not, you can not write.                 
         """},
]

CONCLUSION_SUMMARY_PROMPT_MESSAGES = [
    {"role": "system",
     "content": "You are a reviewer in the field of [{key_words}] and you need to critically review this "
                "article"},
    {"role": "assistant",
     "content": "This is the <summary> and <conclusion> part of an English literature, where <summary> you have "
                "already summarized, but <conclusion> part, I need your help to summarize the following "
                "questions: {clip_text}"},
    {"role": "user", "content": """                 
           7. Make the following summary.
              - (1):What is the significance of this piece of work?
              - (2):Summarize the strengths and weaknesses of this article in three dimensions: innovation point, 
              performance, and workload.                   
              .......
           Follow the format of the output later: 
           7. Conclusion: \n\n
              - (1):xxx;\n                     
              - (2):Innovation point: xxx; Performance: xxx; Workload: xxx;\n                      

           Be sure to statements as concise and academic as possible, do not repeat the content of the previous 
           <summary>, the value of the use of the original numbers, be sure to strictly follow the format, the 
           corresponding content output to xxx, in accordance with \n line feed, ....... means fill in according 
           to the actual requirements, if not, you can not write.                 
           """},
]
