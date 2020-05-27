import numpy as np
import tensorlayer as tl
import tensorflow as tf
from tensorlayer.models.seq2seq import Seq2seq
import pickle


class Predictor():
    def __init__(self):
        #data preprocessing
        metadata, trainX, trainY, testX, testY, validX, validY = self.initial_setup()

        # Parameters
        src_len = len(trainX)
        tgt_len = len(trainY)

        assert src_len == tgt_len

        batch_size = 32
        n_step = src_len // batch_size
        src_vocab_size = len(metadata['idx2w']) # 8002 (0~8001)
        emb_dim = 1024

        self.word2idx = metadata['w2idx']   # dict  word 2 index
        self.idx2word = metadata['idx2w']   # list index 2 word

        self.unk_id = self.word2idx['unk']   # 1
        pad_id = self.word2idx['_']     # 0

        self.start_id = src_vocab_size  # 8002
        end_id = src_vocab_size + 1  # 8003

        self.word2idx.update({'start_id': self.start_id})
        self.word2idx.update({'end_id': end_id})
        self.idx2word = self.idx2word + ['start_id', 'end_id']

        src_vocab_size = tgt_vocab_size = src_vocab_size + 2

        vocabulary_size = src_vocab_size
        
        self.model_ = Seq2seq(
            decoder_seq_length = 20,
            cell_enc=tf.keras.layers.GRUCell,
            cell_dec=tf.keras.layers.GRUCell,
            n_layer=3,
            n_units=256,
            embedding_layer=tl.layers.Embedding(vocabulary_size=vocabulary_size, embedding_size=emb_dim),
        )
        
        load_weights = tl.files.load_npz(name='for_adis/classes/model.npz')
        tl.files.assign_weights(load_weights, self.model_)

    def load_data(self, PATH=''):
        # read data control dictionaries
        with open(PATH + 'metadata.pkl', 'rb') as f:
            metadata = pickle.load(f)
        # read numpy arrays
        idx_q = np.load(PATH + 'idx_q.npy')
        idx_a = np.load(PATH + 'idx_a.npy')
        return metadata, idx_q, idx_a

    def split_dataset(self, x, y, ratio = [0.7, 0.15, 0.15] ):
        # number of examples
        data_len = len(x)
        lens = [ int(data_len*item) for item in ratio ]

        trainX, trainY = x[:lens[0]], y[:lens[0]]
        testX, testY = x[lens[0]:lens[0]+lens[1]], y[lens[0]:lens[0]+lens[1]]
        validX, validY = x[-lens[-1]:], y[-lens[-1]:]

        return (trainX,trainY), (testX,testY), (validX,validY)

    def initial_setup(self):
        metadata, idx_q, idx_a = self.load_data(PATH='for_adis/classes/data/')
        (trainX, trainY), (testX, testY), (validX, validY) = self.split_dataset(idx_q, idx_a)
        trainX = tl.prepro.remove_pad_sequences(trainX.tolist())
        trainY = tl.prepro.remove_pad_sequences(trainY.tolist())
        testX = tl.prepro.remove_pad_sequences(testX.tolist())
        testY = tl.prepro.remove_pad_sequences(testY.tolist())
        validX = tl.prepro.remove_pad_sequences(validX.tolist())
        validY = tl.prepro.remove_pad_sequences(validY.tolist())
        return metadata, trainX, trainY, testX, testY, validX, validY

    def predict(self, seed, top_n):
        self.model_.eval()
        seed_id = [self.word2idx.get(w, self.unk_id) for w in seed.split(" ")]
        sentence_id = self.model_(inputs=[[seed_id]], seq_length=20, start_token=self.start_id, top_n = top_n)
        sentence = []
        for w_id in sentence_id[0]:
            w = self.idx2word[w_id]
            if w == 'end_id':
                break
            word = w.strip()
            if word != 'unk':
                sentence = sentence + [word]
            
        return sentence