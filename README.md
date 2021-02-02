# Named Entity Service

Sören Räuchle, Nadav Babai | [3pc GmbH](https://www.3pc.de)

This service is analysing text for extracting Named Entities, Linked Entities, Abbreviations and Sentiment Scores for the german language.

[Service Documentation](https://www.overleaf.com/read/mdbgvfqpqvmg)

### Technology Stack
- [Python 3.7](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Conda](https://www.anaconda.com/)
- [Spacy](https://spacy.io/)
- [SciSpacy](https://github.com/allenai/scispacy)

### Frontend
The Frontend is injected inside the ```ner_service/templates folder```.

### Named Entities
The Named Entities are a hybrid of AI and Gazetter Dictionaty matching. 
The AI is looking for the Grammar and is using a Spacy Model. The Gazetter Matching is based on Entities extracted from the 3pc.de Website.

### Abbreviation Detection
The Abbreviation Detection is based a Algorithm described in a Paper of A.S. Schwartz and M.A. Hearst. 
Additionally the Detection is extracting Abbreviations from HTML Content.

### Sentiment Analysis
Sentiment Analysis is done with a Sentiment Dictionary for the german language in combination with a lemmatizer.

### PyCharm IDE and Conda Setup
To see fully gets the logs make sure to: 
##### Run > Edit Configuration >  Emulate terminal in output console
Install the environment with: 
```
conda env create -f environment.yml
```
Update the environment with: 
```
conda env update -f environment.yml
```

### Papers
- [A Simple Algorithm for Identifying Abbreviation Definitions in Biomedical Text](https://psb.stanford.edu/psb-online/proceedings/psb03/schwartz.pdf)


### Use case diagram , Named Entity Recognition.
```plantuml
@startuml
:Admin: as Admin
:User: as User 


usecase loadData as "Load text data and entites for model/s"
usecase custom_kb as "create knowledge base
--
Prepare KB´s for Entity Linker Model"

usecase train_entity_linker as "Train Entity Linker model"
usecase model as "Model"
usecase test_model as "Test the model"
usecase sumbit_text as "Submit text"
usecase show_entities as "Show entities
--
Including: enitiy type, link to description, position in text
(Wikidata, Custom Knowledge base Database)"

Admin -right-> loadData  
loadData  -down-> custom_kb
custom_kb -down->  train_entity_linker
train_entity_linker -down-> test_model: predict
test_model -left-> train_entity_linker :update model
test_model -right-> model 


User -left-> sumbit_text
sumbit_text -left-> model  
model -down-> show_entities
@enduml
```

