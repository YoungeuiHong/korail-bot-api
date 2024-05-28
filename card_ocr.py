from google.cloud import documentai_v1beta3 as documentai
from google.protobuf.json_format import MessageToDict
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
PROCESSOR_ID = os.getenv("GOOGLE_CLOUD_PROCESSOR_ID")

def process_document(content: bytes):
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    client = documentai.DocumentProcessorServiceClient()
    name = f'projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}'

    document = documentai.types.RawDocument(content=content, mime_type='image/jpeg')
    request = documentai.types.ProcessRequest(name=name, raw_document=document)
    result = client.process_document(request=request)

    document = result.document
    document_dict = MessageToDict(document._pb)

    card_info = {
        "card_number": None,
        "expiry_date": None,
        "cvc": None,
    }

    for entity in document_dict.get('entities', []):
        if entity['type'] == 'CARD_NUMBER':
            card_info['card_number'] = entity['mentionText']
        elif entity['type'] == 'EXPIRATION_DATE':
            card_info['expiry_date'] = entity['mentionText']
        elif entity['type'] == 'CVC':
            card_info['cvc'] = entity['mentionText']

    return card_info
