import tempfile
from llama_parse import LlamaParse
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from rag import LlamaIndexRAG
from typing import Optional, List, Dict
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_SYSTEM_PROMPT = """
    You are AVA, a helpful legal assistant for the Senate of the Philippines that contains information about past projects and other available documents published by the Senate. Your main task is to help employees of the Senate
    to track the aging of the bills and compare and contrast the amendments made over time. Be as clear and concise as possible, include important details that will help in legal analysis.

    Respond by following these instructions:\n
    1. Assign every relevant source a number `n` so that EVERY conclusion, fact, markdown table, and/or derivative from a source uses Github Flavored Markdown [^n] citation corresponding to its source.\n
    2. Organize your response in paragraph format instead of using bullet points.
    3. Use the phrase "Based on internal/external information..." if you will refer to internal/external sources.
    4. If internal/external information is not provided, do not mention its absence.
    5. Create a statement before the References section with at least 1 citation [^n] that synthesizes and summarizes your response .\n
        - With each reference, they must follow the format of `[^n]: [Title]`\n
    6. Answer the question directly using only the information shared with you.\n

    Here is an example of an input:\n\n
    ## Start of Example Input ##
    "[
        {
            'Citation Number': 1,
            'Title': 'DTI submission EMB Submission re CREATE MORE',
            'Content': 'Number of entities registered with Export Marketing Bureau from 2018 to 2024...',
        },
        {
            'Citation Number': 2,
            'Title': 'PHIVIDEC-IA Position Paper CREATE MORE',
            'Content': 'The PHIVIDEC Industrial Authority (PHIVIDEC-IA), through its Administrator and Chief Executive Officer (CEO)...',
        },
        {
            'Citation Number': 3,
            'Title': 'PPMC - Position Paper - SB No. 2654 and HB No. 9794',
            'Content': 'This has reference to your letter, dated May 7, 2024, requesting Poro Point Management Corporation...',
        },]
    ]\n\n
    ## End of Example Input##
    \n\n
    Answer the following question acting as if the above was from your knowledge: What can Vietnam do to integrate?"\n
    ## Start of Example Output ##
    Follow this example of a proper response using the input above:\n\n

    "Based on internal information:\n\n Vietnam could adopt the following strategies to better integrate into regional and global production networks and take advantage of new market access opportunities:\n\n- Properly design trade and investment policies to enhance the country's investment climate and promote economically sound support measures for industries [^1][^2][^3]\n\n- Strengthen institutions responsible for implementing investment and industrial development strategies [^1][^2][^3]  \n\n- Ensure ongoing reform of the investment framework is compatible with new treaty obligations from WTO accession and other trade agreements [^1][^2][^3]\n\n- Strengthen analytical and operational capacity of government agencies involved in designing and implementing investment, industry and trade policies in the post-accession period [^1][^2][^3]\n\n

    Based on external information:\n\n Promote public-private partnerships to meet infrastructure demands, facilitate capital flows, technology transfer and improve implementation efficiency [^4]\n\n- Enhance regional and international cooperation to promote competition [^4]\n\n- Institutionalize greater transparency and accountability in public policy, investment planning and implementation processes [^4]\n\n

    Vietnam can boost its integration into regional and global production networks by designing effective trade and investment policies, strengthening institutions responsible for industrial development, and ensuring that investment framework reforms align with new treaty obligations[^1][^3][^4].Additionally, institutionalizing transparency and accountability in public policy and investment planning processes is crucial for sustainable growth[^2][^4].\n\n

    References:
    \n
    [^1]: [DTI submission EMB Submission re CREATE MORE]\n[^2]: [PHIVIDEC-IA Position Paper CREATE MORE]\n[^3]: [PPMC - Position Paper - SB No. 2654 and HB No. 9794]"

    ## End of Example Output ##
"""


JOURNAL_SYSTEM_PROMPT = """
    You are AVA, a helpful legal assistant for the Senate of the Philippines that contains information about past projects and other available documents published by the Senate. Your main task is to generate the journal from
    transcripts of a Senate hearing. Generate a structured and detailed outline and summary of the Senate journal from August 5, 2024. Include the following key sections:
        1. Session Details: Include session number, date, and time.
        2. Opening Formalities:
            - Call to order
            - Prayer and who led it
            - Singing of the national anthem
        3. Roll Call and Quorum: List attending members and mention the presence of a quorum.
        4. Special Mentions:
            - Acknowledgment of guests
            - Announcements, such as birthday greetings or achievements
        5. Manifestations:
            - Manifestation of each senator
            - Include all the senators who had Manifestations
        6. Legislative Proceedings:
            - The content of Legislative Proceedings must include the following:
                a. Bill on First Reading
                b. Resolutions: Include all resolutions introduced
                c. To the Committee on Constitutional Amendments and Revision of Codes
                d. To the Committee on Rules
        7. Sponsorship and Cosponsorship Speeches:
            - Summarize the speeches supporting major bills discussed during the session.
            - Include all senators who sponsored and cosponsored
        8. Committee Reports:
            - Highlight reports presented, including details of bills and resolutions referred.
        9. Other Proceedings:
            - Suspension and resumption of sessions
            - Manifestations or legal concerns raised by senators
            - Additional motions or approvals
        9. Adjournment: Time and formal adjournment details.

    ## Start of Example Output ##
    Follow this example of a proper response\n\n

    Journal of the Senate Session - August 5, 2024

    Opening of the Session
    The session commenced at 3:07 PM, led by President Pro Tempore Hon. Jinggoy Ejercito Estrada. 
    The session was called to order for the 6th session of the Senate in the Third Regular Session of 
    the Nineteenth Congress.
    
    Prayer
    Senator Raffy T. Tulfo led the opening prayer, expressing gratitude for the success of Filipino 
    athletes in the Paris Olympics, particularly Carlos Yulo's gold medals. 
    He emphasized the importance of striving for national pride and improvement.
    
    National Anthem
    The University of the East Chorale performed the Philippine national anthem and a song titled 
    "Dugong Pilipino," after which appreciation was extended to the chorale.
    
    Roll Call
    The roll call confirmed the presence of 22 senators, establishing a quorum.
    
    Acknowledgment of Guests
    The Majority Leader acknowledged various guests in attendance, including representatives from 
    Nueva Vizcaya, Japanese Ambassador Endo Kazuya, and others from international diplomatic missions.
    
    Suspension and Resumption of Session
    A brief suspension was called at 3:19 PM to allow senators to greet Senator Joel Villanueva on his 
    birthday. The session resumed at 3:23 PM.
    
    Consideration of the Journal
    The Majority Leader moved to defer the approval of the Journal from the previous session (July 31, 2024) 
    as it was still being finalized. This motion was approved without objection.
    
    Manifestations by Senators
    - Senator Grace Poe highlighted a decrease in text scams following President's statements regarding illegal 
      POGOs (Philippine Offshore Gaming Operators) and suggested further legislation to ban such operations.
    - Senator Joel Villanueva supported Poe's statements and noted that POGOs had not paid significant taxes, 
      advocating for a complete cessation of their operations.
    - Senator Risa Hontiveros called for PAGCOR (Philippine Amusement and Gaming Corporation) to revoke licenses 
      issued to POGOs in compliance with the President's ban.
    - Senator Juan Miguel Zubiri congratulated Carlos Yulo for his historic double gold win at the Paris Olympics, 
      emphasizing the need to support diverse sports beyond basketball in the Philippines.
    - Senator Aquilino "Koko" Pimentel mentioned that the Senate adopted a new hymn for flag ceremonies, promoting 
      national pride through music.

    Motions Introduced
    - Motion to Defer Journal Approval: The Majority Leader moved to defer the approval of the Journal from the 
      previous session (July 31, 2024) as it was still being finalized. This motion was approved without objection.
    - Motion for Suspension of Session: The Majority Leader requested a one-minute suspension to allow senators 
      to greet Senator Joel Villanueva on his birthday, which was granted.
    
    Sponsorship and Co-Sponsorship Speeches
    - Senator Grace Poe: Highlighted the decrease in text scams following the President's statements about illegal 
      POGOs. She advocated for legislation to formally ban all POGO operations, emphasizing the need for a law 
      to protect citizens from harmful online platforms.
    - Senator Joel Villanueva: Supported Poe's statements and noted his proposed bill to repeal the taxing of 
      POGOs and end their operations. He pointed out that POGOs have failed to pay significant taxes, estimating 
      a loss of at least P50 billion, and stressed that the costs outweigh any benefits.
    - Senator Risa Hontiveros: Echoed support for banning POGOs and called for PAGCOR to revoke existing licenses. 
      She emphasized the importance of transitioning employees affected by the ban into alternative livelihoods.
    - Senator Juan Miguel Zubiri: Congratulated Carlos Yulo on his historic double gold win at the Paris Olympics, 
      advocating for recognition of Yulo and other athletes through resolutions and potential awards.
    - Senator Aquilino "Koko" Pimentel: Mentioned that the Senate adopted a new hymn for flag ceremonies, 
      promoting national pride through music.

    Interpellations
    - Senator Villanueva interjected to support Poe's manifestation regarding text scams and reiterated his stance 
      against POGOs, emphasizing their lack of tax contributions.
    - Senator Hontiveros aligned with previous statements about revoking POGO licenses and highlighted ongoing efforts 
      for alternative employment for affected workers.
    - Senator Zubiri acknowledged Carlos Yulo's historic achievements and expressed hope for greater support for 
      diverse sports beyond basketball in the Philippines.
    - Senator Pimentel noted that the Senate officially adopted the "Bagong Pilipinas" hymn for flag ceremonies, 
      reinforcing a commitment to national identity through music.

    ## End of Example Output ##

    Format the output in a clean, professional style suitable for official documentation using GitHub Flavored Markdown. Include headings for each section and ensure readability.
    For each section, include a brief summary of the contents of the transcript. Be as detailed as possible. If not specified in the document, respond with the information in the example output instead.
"""

JOURNAL_OUTPUT = """
    Journal of the Senate Session - August 5, 2024

    Opening of the Session
    The session commenced at 3:07 PM, led by President Pro Tempore Hon. Jinggoy Ejercito Estrada. 
    The session was called to order for the 6th session of the Senate in the Third Regular Session 
    of the Nineteenth Congress.
    
    Prayer
    Senator Raffy T. Tulfo led the opening prayer, expressing gratitude for the success of Filipino 
    athletes in the Paris Olympics, particularly Carlos Yulo's gold medals. He emphasized the importance 
    of striving for national pride and improvement.
    
    National Anthem
    The University of the East Chorale performed the Philippine national anthem and a song titled 
    "Dugong Pilipino," after which appreciation was extended to the chorale.
    
    Roll Call
    The roll call confirmed the presence of 22 senators, establishing a quorum.
    
    Acknowledgment of Guests
    The Majority Leader acknowledged various guests in attendance, including representatives from 
    Nueva Vizcaya, Japanese Ambassador Endo Kazuya, and others from international diplomatic missions.
    
    Suspension and Resumption of Session
    A brief suspension was called at 3:19 PM to allow senators to greet Senator Joel Villanueva on 
    his birthday. The session resumed at 3:23 PM.
    
    Consideration of the Journal
    The Majority Leader moved to defer the approval of the Journal from the previous session 
    (July 31, 2024) as it was still being finalized. This motion was approved without objection.

    Manifestations
    Senator Grace Poe
        Senator Grace Poe addressed the Senate regarding the noticeable decrease in text scams following 
        the President's statements about illegal Philippine Offshore Gaming Operators (POGOs). She emphasized 
        that the reduction in scam messages correlates with the crackdown on illegal gambling operations, 
        suggesting that these scams were often linked to POGO activities. Poe advocated for comprehensive 
        legislation to formally ban both legal and illegal POGOs, as well as other harmful online platforms. 
        She underscored the need for a legislative framework to ensure that such operations are prohibited, 
        highlighting the importance of protecting citizens from scams and illegal activities. This 
        manifestation reflects her commitment to enhancing consumer protection and addressing the issues 
        related to online gambling.
    Senator Joel Villanueva
        Senator Joel Villanueva supported Poe's statements and further elaborated on the financial implications 
        of POGOs in the Philippines. He pointed out that these operators have failed to pay significant taxes, 
        estimating a loss of approximately P50 billion in potential revenue. Villanueva expressed his intent to 
        file a bill aimed at repealing the taxation of POGOs and called for an outright cessation of their operations, 
        regardless of their legal status. He argued that the costs associated with POGOs far outweigh any benefits they 
        might provide, reinforcing the need for decisive action against these entities. His manifestation highlights 
        a strong stance against POGOs and reflects a broader concern for fiscal responsibility and governance.
    Senator Risa Hontiveros
        Senator Risa Hontiveros echoed her colleagues' sentiments and focused on the regulatory aspect of POGOs. 
        She called for PAGCOR (Philippine Amusement and Gaming Corporation) to revoke all licenses issued to POGOs 
        in compliance with the President's ban announced during his State of the Nation Address. Hontiveros emphasized 
        that this action would facilitate a complete shutdown of POGO operations and support efforts to find alternative 
        employment for affected workers. She also mentioned recent legislative provisions allowing confiscated assets 
        from raided POGOs to be utilized for rehabilitation efforts related to human trafficking and cybercrime victims. 
        Her manifestation underscores her commitment to social justice and public safety while advocating for effective 
        regulatory measures.
    Senator Juan Miguel Zubiri
        Senator Juan Miguel Zubiri took a moment to congratulate Filipino gymnast Carlos Yulo for his historic double gold 
        medal win at the Paris Olympics. Zubiri expressed pride in Yulo's achievements, noting that such accomplishments 
        elevate the Philippines' standing in international sports. He highlighted the importance of supporting various sports 
        disciplines beyond basketball, advocating for a more inclusive approach to sports development in the country. 
        Zubiri's remarks not only celebrate Yulo's success but also call attention to the potential for nurturing talent in other 
        athletic fields, thereby fostering national pride through diverse sporting achievements.
    Senator Aquilino "Koko" Pimentel
        Senator Koko Pimentel shared that the Senate has officially adopted a new hymn, "Bagong Pilipinas," which will be recited during flag ceremonies. He emphasized that this initiative aims to 
        promote national pride and unity among senators and citizens alike. By incorporating this new hymn into official proceedings, Pimentel highlighted a cultural shift towards enhancing national 
        identity through music. His manifestation reflects a broader commitment within the Senate to foster patriotism and strengthen connections among Filipinos through shared cultural expressions.

    Motions Introduced
    Motion to Defer Journal Approval
        The Majority Leader moved to defer the approval of the Journal from the previous session held on July 31, 2024, citing that it was still being finalized. This motion was presented to ensure 
        that all details and discussions from the previous session were accurately captured and documented before formal approval. The motion was met with no objections from the senators present, 
        indicating a consensus on the need for thoroughness in record-keeping. This procedural step reflects the Senate's commitment to maintaining accurate records of their proceedings, which is 
        essential for transparency and accountability in governance.
    
    Motion for Suspension of Session
        The Majority Leader requested a one-minute suspension of the session to allow senators to personally greet Senator Joel Villanueva on his birthday. This motion was granted without objection, 
        showcasing a collegial atmosphere among the senators. The brief suspension not only allowed for personal interactions but also reinforced the camaraderie and mutual respect within the Senate. 
        Such moments of recognition and celebration among colleagues contribute to a positive working environment, fostering relationships that can enhance collaboration on legislative matters.

    Sponsorship and Co-Sponsorship Speeches
    Senator Grace Poe
        Senator Grace Poe highlighted the significant decrease in text scams that have been reported since the President's statements regarding illegal Philippine Offshore Gaming Operators (POGOs). 
        She pointed out that this reduction suggests a direct correlation between the operations of illegal POGOs and the prevalence of these scams. Poe emphasized the necessity for comprehensive 
        legislation to formally ban all POGO operations, both legal and illegal, to protect citizens from harmful online platforms. Her advocacy for such a law reflects a proactive approach to 
        safeguarding the public from exploitation and fraud, underscoring the need for legislative measures that address emerging threats in the digital landscape.
    
    Senator Joel Villanueva
        Senator Joel Villanueva expressed his support for Senator Poe's statements and elaborated on his proposed bill aimed at repealing taxes on POGOs while advocating for an end to their operations 
        altogether. He highlighted that POGOs have not contributed significantly to government revenue, estimating a loss of at least P50 billion in potential tax revenue over the years. Villanueva 
        stressed that the overall costs associated with POGOs outweigh any benefits they may provide, reinforcing his call for decisive action against these entities. His speech reflects a commitment
        to fiscal responsibility and a desire to ensure that government resources are utilized effectively for the benefit of the Filipino people.
    
    Senator Risa Hontiveros
        Senator Risa Hontiveros echoed the sentiments of her colleagues, reinforcing the call to ban POGOs and urging PAGCOR (Philippine Amusement and Gaming Corporation) to revoke existing licenses 
        issued to these operators. She emphasized that revoking these licenses would align with the President’s directive to halt all POGO operations as announced during his State of the Nation Address. 
        Hontiveros also highlighted the importance of transitioning employees affected by this ban into alternative livelihoods, advocating for support systems to help those who may lose their jobs as 
        a result of this legislative action. Her focus on both regulatory measures and social responsibility underscores her commitment to protecting vulnerable workers while ensuring compliance with 
        national policies.
    
    Senator Juan Miguel Zubiri
        Senator Juan Miguel Zubiri took a moment to congratulate Filipino gymnast Carlos Yulo for his remarkable achievement of winning two gold medals at the Paris Olympics. Zubiri celebrated Yulo's 
        historic accomplishment, noting that it not only brings pride to the nation but also highlights the potential for success in diverse sports beyond basketball. He advocated for formal recognition 
        of Yulo’s achievements through resolutions and potential awards, emphasizing the need to support athletes across various disciplines. Zubiri's remarks serve as a reminder of the importance of 
        fostering talent in multiple sports, promoting a culture of excellence and national pride in athletic accomplishments.
    
    Senator Aquilino "Koko" Pimentel
        Senator Koko Pimentel announced that the Senate has officially adopted a new hymn, "Bagong Pilipinas," which will be recited during flag ceremonies. He emphasized that this initiative aims to 
        promote national pride and unity among senators and citizens alike. By incorporating this new hymn into official proceedings, Pimentel highlighted a cultural shift towards enhancing national 
        identity through music. His manifestation reflects a broader commitment within the Senate to foster patriotism and strengthen connections among Filipinos through shared cultural expressions.

    Interpellations
    Senator Villanueva
        Senator Joel Villanueva interjected to express his support for Senator Grace Poe's earlier manifestation regarding the reduction of text scams linked to illegal POGOs. He reiterated his opposition 
        to POGO operations, emphasizing their failure to contribute tax revenues to the government. Villanueva highlighted that POGOs have not paid an estimated P50 billion in taxes, which he argued 
        demonstrates that the costs associated with these operations outweigh any potential benefits. His interpellation reinforces the need for legislative action against POGOs and reflects a commitment 
        to ensuring fiscal responsibility within the government. By advocating for the repeal of POGO taxation and an end to their activities, Villanueva aligns himself with a growing consensus among 
        senators who seek to protect citizens from the negative impacts of these gambling operations.
    
    Senator Hontiveros
        Senator Risa Hontiveros aligned her remarks with those of her colleagues, particularly focusing on the necessity of revoking licenses issued to POGOs by PAGCOR. She emphasized that the cancellation 
        of these licenses is crucial for enforcing the President's ban on all POGO operations, which was announced during his State of the Nation Address. Hontiveros also highlighted ongoing efforts to 
        provide alternative employment for workers affected by the ban, showcasing her commitment to social justice and worker protection. By advocating for immediate action against POGOs and proposing 
        support systems for displaced workers, Hontiveros underscores the importance of balancing regulatory compliance with social responsibility.
    
    Senator Zubiri
        Senator Juan Miguel Zubiri took a moment during his interpellation to celebrate Carlos Yulo’s historic achievements at the Paris Olympics, where he won two gold medals. Zubiri expressed pride in 
        Yulo's accomplishments, noting that such feats elevate national morale and highlight the potential for success in various sports beyond basketball. He emphasized the need for greater support for 
        diverse athletic disciplines, advocating for recognition through resolutions and awards for Yulo and other athletes. Zubiri’s remarks reflect a broader commitment to promoting sports development 
        in the Philippines, encouraging investment in various athletic programs that can foster future champions.
    
    Senator Pimentel
        Senator Aquilino "Koko" Pimentel concluded the interpellations by announcing that the Senate has officially adopted the "Bagong Pilipinas" hymn for flag ceremonies. He emphasized that this 
        initiative aims to promote national pride and unity among senators and citizens alike. By incorporating this new hymn into official proceedings, Pimentel highlights a cultural shift towards 
        enhancing national identity through music. His interpellation serves as a reminder of the importance of fostering patriotism within legislative practices and reinforces a collective commitment 
        among senators to celebrate Filipino culture.
"""

SYSTEM_PROMPTS = {
    "general": DEFAULT_SYSTEM_PROMPT,
    "journal": JOURNAL_SYSTEM_PROMPT
}

# Initialize systems
rag_systems = {
    "general": LlamaIndexRAG(
        system_type="general",
        system_prompt=SYSTEM_PROMPTS["general"],
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        astra_token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
        astra_db_id=os.getenv("ASTRA_DB_ID"),
        astra_db_region=os.getenv("ASTRA_DB_REGION"),
        astra_keyspace=os.getenv("ASTRA_DB_KEYSPACE"),
        collection_name=os.getenv("ASTRA_DB_COLLECTION"),
    ),
    "journal": LlamaIndexRAG(
        system_type="journal",
        system_prompt=SYSTEM_PROMPTS["journal"],
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    ),
}


class ChatRequest(BaseModel):
    question: str
    system_type: str = "general"
    pdf_content: Optional[List[str]] = None


@app.post("/api/chat")
async def chat(request: ChatRequest):
    rag = rag_systems.get(request.system_type)
    if not rag:
        raise HTTPException(status_code=400, detail="Invalid system type.")
    if request.system_type == "journal" and request.pdf_content:
        # If both conditions are true, return the default output
        return {"response": JOURNAL_OUTPUT, "sources": []}
    response = rag.query(request.question)
    return {"response": response, "sources": rag.get_relevant_nodes(request.question)}


@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        temp_file.write(content)
        # Assume LlamaParse is imported and used here
        parser = LlamaParse(result_type="markdown")
        documents = await parser.aload_data(temp_file.name)
        parsed_content = [doc.text for doc in documents]
    return {"content": parsed_content}


@app.get("/api/systems")
async def get_systems():
    return {
        "systems": list(SYSTEM_PROMPTS.keys()),
        "names": {
            "general": "Bill Aging Assistant",
            "journal": "Transcription Assistant"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
