import torch

from hw1.src.task7 import (
    Translator, build_vocab, decoder_input, encode, tokenize, train_epoch, translate,
)


def test_tokenize():
    assert tokenize("I am happy!") == ["i", "am", "happy"]


def test_build_vocab():
    vocab = build_vocab(["i am happy", "i am tired"])
    assert vocab == {
        "<unk>": 0, "<bos>": 1, "<eos>": 2,
        "i": 3, "am": 4, "happy": 5, "tired": 6,
    }


def test_encode():
    vocab = build_vocab(["i am happy"])
    tensor = encode("i am happy", vocab)
    assert tensor.tolist() == [[3, 4, 5, 2]]
    assert tensor.dtype == torch.long


def test_encode_unknown_word():
    vocab = build_vocab(["i am happy"])
    assert encode("i am tired", vocab).tolist() == [[3, 4, 0, 2]]


def test_decoder_input():
    target = torch.tensor([[3, 4, 2]])
    assert decoder_input(target).tolist() == [[1, 3, 4]]


def test_translator_output_shape():
    model = Translator(english_size=6, italian_size=5)
    english = torch.tensor([[3, 4, 5, 2]])
    italian_input = torch.tensor([[1, 3, 4]])
    assert model(english, italian_input).shape == (1, 3, 5)


def test_english_to_italian_translation():
    # Checks learning a known pair, not translation of unseen sentences.
    torch.manual_seed(7)
    english_vocab = build_vocab(["i am happy"])
    italian_vocab = build_vocab(["sono felice"])
    examples = [
        (
            encode("i am happy", english_vocab),
            encode("sono felice", italian_vocab),
        )
    ]

    model = Translator(len(english_vocab), len(italian_vocab))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = torch.nn.CrossEntropyLoss()

    for _ in range(100):
        train_epoch(model, examples, optimizer, loss_fn)

    result = translate(model, "i am happy", english_vocab, italian_vocab)
    assert result == "sono felice"
