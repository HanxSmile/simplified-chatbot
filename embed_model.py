import torch
from transformers import AutoTokenizer, AutoModel
import torch.nn as nn
from torch import Tensor


class EmbedModel(nn.Module):
    def __init__(
            self,
            model_name
    ):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        self.task = 'Given a web search query, retrieve relevant passages that answer the query'
        self.embed_dim = self.model.config.hidden_size

    @staticmethod
    def last_token_pool(last_hidden_states: Tensor,
                        attention_mask: Tensor) -> Tensor:
        left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
        if left_padding:
            return last_hidden_states[:, -1]
        else:
            sequence_lengths = attention_mask.sum(dim=1) - 1
            batch_size = last_hidden_states.shape[0]
            return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

    @staticmethod
    def get_detailed_instruct(task_description: str, query: str) -> str:
        return f'Instruct: {task_description}\nQuery: {query}'

    def encode(self, sentence):
        batch_dict = self.tokenizer(sentence, max_length=512, padding=True, truncation=True, return_tensors='pt')
        outputs = self.model(**batch_dict)
        embeddings = self.last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
        return embeddings.detach().cpu().numpy()

    def encode_query(self, sentence):
        sentence = self.get_detailed_instruct(self.task, sentence)
        return self.encode(sentence)
