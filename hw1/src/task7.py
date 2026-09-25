"""Task 7: 
I had Codex create a guided English -> Italian translation exercise to practice
using pytorch for extremely basic machine learning

Run now: stage 0 works. Complete TODOs in order and increase STAGE after each.
NotImplementedError means you reached an exercise you still need to complete.

English -> word IDs -> encoder -> sentence memory -> decoder -> Italian IDs

Tensor = numerical array. Model = operations with learnable parameters.
Loss = prediction error. Gradient = how a parameter affects that error.
Optimizer = algorithm that changes parameters using their gradients.

Read alongside this file:
https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html
https://docs.pytorch.org/tutorials/beginner/basics/buildmodel_tutorial.html
https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html
https://docs.pytorch.org/tutorials/intermediate/seq2seq_translation_tutorial.html

"""

from pathlib import Path
import random
import re

import torch
from torch import nn

STAGE = 6  # Change to 1, 2, ... 6 as you implement each numbered exercise.
EPOCHS = 100  # One epoch = one pass through all training examples.
EMBED_SIZE = 16  # Learned numbers representing each word.
HIDDEN_SIZE = 32  # Numbers in the GRU's sentence memory.
LEARNING_RATE = 0.01  # Controls update size; experiment later.

# Authored practice data
PRACTICE_PAIRS = [
    ("i am happy", "sono felice"),
    ("i am tired", "sono stanco"),
    ("i am ready", "sono pronto"),
    ("you are happy", "sei felice"),
    ("you are tired", "sei stanco"),
    ("you are ready", "sei pronto"),
    ("hello", "ciao"),
    ("thank you", "grazie"),
]
UNK, BOS, EOS = 0, 1, 2
SPECIALS = {"<unk>": UNK, "<bos>": BOS, "<eos>": EOS}
# UNK = unknown word; BOS/EOS = beginning/end of sentence.

def tokenize(sentence):
    r"""TODO 1: return lowercase words as a Python list.

    Check: tokenize("I am happy!") == ["i", "am", "happy"].
    No torch yet: we must prepare text before a model can use it.
    """

    lower_sentence = sentence.lower()
    tokens = re.findall(r"\w+", lower_sentence)
    return tokens


def build_vocab(sentences):
    """TODO 2a: map each distinct word to a unique integer."""

    vocab = SPECIALS.copy()
    for sentence in sentences:
        for word in tokenize(sentence):
            if word not in vocab:
                vocab[word] = len(vocab)

    return vocab


def encode(sentence, vocab):
    """TODO 2b: convert words to IDs, append EOS, return a tensor.

    Check: 'i am happy' becomes shape (1, 4), with EOS in the last position.
    """

    ids = []

    for word in tokenize(sentence):
        ids.append(vocab.get(word, UNK))

    ids.append(EOS)
    tensor = torch.tensor(ids, dtype=torch.long)

    return tensor.unsqueeze(0)


def decoder_input(target):
    """TODO 3: shift the correct Italian sequence one position right.

    target: [sono, felice, EOS]    <- correct answers for each position
    input:  [BOS,  sono,   felice] <- previous word supplied at each position
    """

    start = torch.tensor([[BOS]], dtype=torch.long)
    previous_words = target[:, :-1]

    return torch.cat((start, previous_words), dim=1)

class Translator(nn.Module):
    """Layers supplied; you connect them in forward.

    Embedding looks up a learned vector for a word ID.
    GRU reads vectors in sequence, maintaining a learned memory.
    Linear converts that memory to one score per Italian vocabulary entry.
    Module registers the layers so model.parameters() finds their weights.
    """

    def __init__(self, english_size, italian_size):
        super().__init__()
        self.english_embedding = nn.Embedding(english_size, EMBED_SIZE)
        self.encoder = nn.GRU(EMBED_SIZE, HIDDEN_SIZE, batch_first=True)
        self.italian_embedding = nn.Embedding(italian_size, EMBED_SIZE)
        self.decoder = nn.GRU(EMBED_SIZE, HIDDEN_SIZE, batch_first=True)
        self.output = nn.Linear(HIDDEN_SIZE, italian_size)

    def forward(self, english, italian_input):
        """TODO 4: connect the layers in roughly five lines.

        1. english_embedding(english): [1, S] -> [1, S, 16].
        2. Pass that into encoder. GRU returns (outputs, hidden); keep hidden.
           hidden is [1, 1, 32]: [layers, batch, memory_size].
        3. italian_embedding(italian_input): [1, T] -> [1, T, 16].
        4. decoder(embedded_italian, hidden); keep its first return value.
        5. Pass decoder outputs through self.output and return the result.
           Result: [1, T, Italian vocabulary size].

        S/T are sentence lengths and may differ. Values are raw scores
        ('logits'). Do NOT apply softmax: CrossEntropyLoss handles that.
        """

        english_vectors = self.english_embedding(english)
        _, hidden = self.encoder(english_vectors)

        italian_vectors = self.italian_embedding(italian_input)
        keep, _ = self.decoder(italian_vectors, hidden)

        return self.output(keep)


def train_epoch(model, examples, optimizer, loss_fn):
    model.train()
    random.shuffle(examples)
    total_loss = 0.0
    for english, target in examples:
        # TODO 5: replace the raise with these operations IN THIS ORDER:
        # a. clear gradients from the previous step.
        # b. predict.
        # c. Shapes: [T, vocabulary_size] scores and [T] correct word IDs.
        #    squeeze(0) removes our one-item batch dimension.
        # d. compute gradients of loss wrt parameters.
        # e. update trainable parameters.
        # f. Add loss.item() to total_loss; item() extracts a Python number.
        # WHY zero_grad? PyTorch accumulates gradients unless cleared.

        optimizer.zero_grad()

        italian_input = decoder_input(target)
        logits = model(english, italian_input)

        loss = loss_fn(logits.squeeze(0), target.squeeze(0))

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(examples)


@torch.no_grad()  # Prediction doesn't need a gradient computation graph.
def translate(model, sentence, english_vocab, italian_vocab, max_words=15):
    """TODO 6: generate a word at a time, stopping at EOS or max_words.

    Setup:
      Encode English; run english_embedding and encoder to obtain hidden.
      Create token.
      Create id_to_word.
      Create an empty Python list for generated words.
    Repeat up to max_words:
      Embed token with italian_embedding, then decoder(embedded, hidden).
      IMPORTANT: keep the returned hidden for the NEXT iteration.
      Use model.output on decoder output; choose argmax(dim=-1).
      That gives token shape [1, 1]; token.item() gets the predicted ID.
      If ID is EOS: break. Otherwise append id_to_word[ID] to your list.
      The next iteration uses this predicted token, not the correct answer.

    eval() switches training-specific layer behavior; no_grad() disables
    gradient tracking. Our model has no dropout, but practice using both.
    The length limit prevents an untrained model from generating forever.
    """
    model.eval()

    english = encode(sentence, english_vocab)
    english_vectors = model.english_embedding(english)
    _, hidden = model.encoder(english_vectors)

    token = torch.tensor([[BOS]], dtype=torch.long)
    words = []

    id_to_word = {
        id_: word
        for word, id_ in italian_vocab.items()
    }

    for _ in range(max_words):
        italian_vector = model.italian_embedding(token)
        decoder_output, hidden = model.decoder(italian_vector, hidden)

        logits = model.output(decoder_output)

        token = logits.argmax(dim=-1)
        predicted_id = token.item()

        if predicted_id == EOS:
            break

        words.append(id_to_word[predicted_id])

    return " ".join(words)


def load_parallel_files(english_path, italian_path, limit=200):
    """Supplied bridge for cleaned local IWSLT2017 en/it plain-text exports.

    Corresponding lines must be translations. Remove XML/talk metadata first;
    raw .xml/.tags files are NOT ready to use. Never shuffle files separately.
    Information: https://wit3.fbk.eu/2017-01
    """
    pairs = []
    with Path(english_path).open(encoding="utf-8") as en_file:
        with Path(italian_path).open(encoding="utf-8") as it_file:
            for en, it in zip(en_file, it_file, strict=True):
                en, it = en.strip(), it.strip()
                if en.startswith("<") or it.startswith("<"):
                    raise ValueError("Use cleaned parallel text, not XML/tags.")
                if en and it and len(tokenize(en)) <= 10 and len(tokenize(it)) <= 10:
                    if len(pairs) < limit:
                        pairs.append((en, it))
    if not pairs:
        raise ValueError("No short, non-empty sentence pairs found.")
    return pairs


def main():
    torch.manual_seed(7)
    random.seed(7)
    if STAGE < 1:
        print("Next: complete TODO 1, set STAGE = 1, and rerun.")
        return
    assert tokenize("I am happy!") == ["i", "am", "happy"]
    print("Stage 1: tokenization works.")
    if STAGE < 2:
        return

    pairs = PRACTICE_PAIRS.copy()
    english_vocab = build_vocab(en for en, it in pairs)
    italian_vocab = build_vocab(it for en, it in pairs)
    examples = [(encode(en, english_vocab), encode(it, italian_vocab))
                for en, it in pairs]
    english, target = examples[0]
    probe = encode("i am happy", english_vocab)
    assert probe.shape == (1, 4) and probe.dtype == torch.long
    assert probe[0, -1].item() == EOS
    assert encode("zzunknownword", english_vocab)[0, 0].item() == UNK
    print("Stage 2 vocabulary:", english_vocab)
    print("First encoded pair:", english, target)
    if STAGE < 3:
        return

    shifted = decoder_input(target)
    assert shifted.shape == target.shape and shifted[0, 0].item() == BOS
    assert torch.equal(shifted[:, 1:], target[:, :-1])
    print("Stage 3 input / target:", shifted, target)
    if STAGE < 4:
        return

    model = Translator(len(english_vocab), len(italian_vocab))
    logits = model(english, shifted)
    assert logits.shape == (1, target.shape[1], len(italian_vocab))
    print("Stage 4 output shape:", logits.shape)
    if STAGE < 5:
        return

    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.CrossEntropyLoss()
    for epoch in range(1, EPOCHS + 1):
        loss = train_epoch(model, examples, optimizer, loss_fn)
        if epoch == 1 or epoch % 10 == 0:
            print(f"Epoch {epoch:3d}: mean training loss = {loss:.4f}")
    # Expect a downward trend, not necessarily a decrease at EVERY step.
    if STAGE < 6:
        return
    for en, it in pairs[:3]:
        print(f"English: {en} | expected: {it}")
        print("Predicted:", translate(model, en, english_vocab, italian_vocab))

if __name__ == "__main__":
    main()
