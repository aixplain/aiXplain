
import os
import logging
os.environ["TEAM_API_KEY"] = "7ecc0942bbebfd941715b8658516661cd3845c7a246ff2e1d12cf53c833b58d2"
os.environ['BACKEND_URL'] = "https://dev-platform-api.aixplain.com"
os.environ["MODELS_RUN_URL"] = "https://dev-models.aixplain.com/api/v1/execute"
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

from aixplain.factories import IndexModelFactory
model = IndexModelFactory.get("66eae6656eb56311f2595011")
data = {"data" : "Test collection 2" , "description": "This is a dummy collection for testing."}
result = model.run(data)
print(result)


# Ingest data
id = result['data']

searchModel =  IndexModelFactory.get(id)
data =[
    {"value": "Ultrasound-guided transversus abdominis plane (TAP) block is an adjunct therapy to provide effective postoperative analgesia in abdominal surgical procedures. Dexamethasone is a supplement agent that can improve the efficacy of local anesthesia. However, information about its additive effect is limited. This study aimed to compare the analgesic efficiency using ultrasound-guided TAP block with and without perineural dexamethasone for patients who underwent laparoscopic cholecystectomy. Sixty patients who underwent laparoscopic cholecystectomy were randomly divided into three groups: group I, controls; group II, TAP; and group III, TAP+perineural dexamethasone supplement. The requirement of additional analgesia and the first-time request of rescue-analgesia were recorded after operation and the numerical rating scale was evaluated at specific intervals. Compared to group I, the first-time requirement of rescue-analgesia in groups II and III was significantly delayed (403.0+/-230.9, 436.0+/-225.3 vs 152.3+/-124.7, P<0.01). Compared with those in group I, patients in groups II and III were associated with lower numerical rating scale pain scores (P<0.01) and less postoperative analgesic consumption (P<0.01). There was no significant difference in the variables mentioned above between groups II and III (P>0.05).",
 "value_type": "text",
 "id": "1",
 "uri": "",
 "attributes": {}},
 {"value": "Creatine is a naturally occurring compound that plays a critical role in energy production within muscle cells. Its supplementation has been extensively studied and is widely recognized for its benefits in improving physical performance, particularly in activities that require short bursts of high-intensity effort, such as weightlifting and sprinting. Creatine helps replenish adenosine triphosphate (ATP), the primary energy currency of the body, enabling faster recovery and enhanced output during repeated bouts of exercise. Beyond athletic performance, creatine may support cognitive function, especially during mentally demanding tasks, and has shown potential in neuroprotective roles for conditions like traumatic brain injuries or neurodegenerative diseases. Additionally, it can promote muscle mass by increasing water retention in muscle cells and supporting muscle protein synthesis, making it valuable for both athletes and individuals seeking to maintain muscle health. Creatine is safe for long-term use and is one of the most researched and effective supplements available.",
 "value_type": "text",
 "uri": "",
 "id": "2",
 "attributes": {}}
]
result = searchModel.ingest(data)
print("Ingest results: ", result)

#Search Data
result = searchModel.search(query="What is creatine?", top_k=10)
print("Search result: ", result)
