import torch
import torch.nn as nn
from transformers import (
    BertTokenizer,
    ViTFeatureExtractor,
    VisionEncoderDecoderModel,
    ViTConfig,
    BertConfig,
    VisionEncoderDecoderConfig
)


class ImgCapModel(nn.Module):
    '''
        Main model:
            Encoder \
                "google/vit-base-patch16-224-in21k" \
                "facebook/convnext-xlarge-384-22k-1k" \

            Decoder \
                "gpt2" \
                "bert-base-uncased" \

            Combined \
                "nlpconnect/vit-gpt2-image-captioning"
    '''

    def __init__(
        self,
        encoder_name="google/vit-base-patch16-224-in21k",
        decoder_name="bert-base-uncased",
        gen_config=None
    ):

        super().__init__()

        # check device
        # self.device = torch.device("cuda")
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print("Using device: ", self.device)

        " sub-tools "
        # tokenizer for decoder
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

        # visual extractor for encoder
        self.image_processor = ViTFeatureExtractor.from_pretrained(
            "google/vit-base-patch16-224-in21k"
        )

        " main model: with config, pretrained encoder, decoder "
        self.model = VisionEncoderDecoderModel.from_encoder_decoder_pretrained(
            encoder_pretrained_model_name_or_path=encoder_name,
            decoder_pretrained_model_name_or_path=decoder_name
        ).to(self.device)

        self.model.config.decoder_start_token_id = self.tokenizer.cls_token_id
        self.model.config.pad_token_id = self.tokenizer.pad_token_id

        # for generation
        self.gen_config = gen_config

    def forward(self, image, caption=None):

        pixel_values = self.image_processor(
            image, return_tensors="pt"
        ).pixel_values.to(self.device)

        labels = self.tokenizer(
            caption,
            return_tensors="pt",
            padding=True,
            truncation=True
        ).input_ids.to(self.device)

        return self.model(pixel_values=pixel_values, labels=labels)

    def inference(self, image):

        gen_kwargs = {**self.gen_config}

        pixel_values = self.image_processor(
            image, return_tensors="pt").pixel_values.to(self.device)

        generated_ids = self.model.generate(pixel_values)

        generated_text = self.tokenizer.batch_decode(
            generated_ids, skip_special_tokens=True)[0]

        return generated_text

    def save_model(self, model_path="model"):
        self.tokenizer.save_pretrained(model_path)
        self.model.save_pretrained(model_path)

    def load_model(self, model_path):
        self.model = VisionEncoderDecoderModel.from_pretrained(model_path)
        self.tokenizer = BertTokenizer.from_pretrained(model_path)
        self.image_processor = ViTFeatureExtractor.from_pretrained(model_path)

        self.model.config.decoder_start_token_id = self.tokenizer.cls_token_id
        self.model.config.pad_token_id = self.tokenizer.pad_token_id
