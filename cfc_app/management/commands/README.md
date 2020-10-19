# Legit-Info Text Analytics

We are using <b>Watson Natural Language Understanding (NLU)</b> as our model here as it has been trained on millions of documents and entities and we wanted to leverage this training. 


## Data Preprocessing (Cleaning)


Our first step before sending the legiscan bill documents to NLU was cleaning the text from these documents by getting rid of single quotes, double quotes, apostrophes and new line chars. We have written a python utility script for this  located at the following path. 

```
Legit-Info/cfc_app/management/commands/scan_json.py
```

## Invoking the NLU model

Once, the function returned returned the cleaned text, we pass this text input to the custom NLU invocation script - at the following path. 
```
Legit-Info/cfc_app/management/commands/analyze_text.py
```

We are looking to extract impact area for each of these legiscan bills, which can be mapped to the underlying concepts of this model. We call the function as below. We can limit the number of concepts to be returned through limit parameter. This is the model invocation command.

```
features = Features(categories=CategoriesOptions(limit=RLIMIT), sentiment=SentimentOptions(), concepts=ConceptsOptions(limit=RLIMIT), keywords=KeywordsOptions(sentiment=True, limit=10), syntax=syntax)
```

<b> Note </b> - there are extra features in this command, but for returning impact area, we would just need concepts attribute specifying a limit on how many concepts we want the model to return.

```
response = natural_language_understanding.analyze(features, text=text, language='en')
```
We get the response in the following format which is further mapped to one of the impact areas desribed in the followngs sections.

```
[{'text': 'Taxation in the United States', 'relevance': 0.989995, 'dbpedia_resource': 'http://dbpedia.org/resource/Taxation_in_the_United_States'}, {'text': 'Taxation', 'relevance': 0.866336, 'dbpedia_resource': 'http://dbpedia.org/resource/Taxation'}, {'text': 'Tax', 'relevance': 0.624919, 'dbpedia_resource': 'http://dbpedia.org/resource/Tax'}, {'text': 'Corporate tax', 'relevance': 0.495772, 'dbpedia_resource': 'http://dbpedia.org/resource/Corporate_tax'}, {'text': 'Value added tax', 'relevance': 0.482119, 'dbpedia_resource': 'http://dbpedia.org/resource/Value_added_tax'}]
```
To learn more about NLU, please follow this link - https://cloud.ibm.com/docs/natural-language-understanding.

## Impact Area Mapping

