from pandas import read_csv
from tensorflow.keras.layers import Embedding, Bidirectional, GlobalMaxPooling1D, Dense, Dropout, LSTM
from tensorflow.keras import Sequential
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical


df = read_csv('./training_data/my_spam_dataset.csv')

X_train, X_test, y_train, y_test = train_test_split(df['text'], df['labels'], test_size=0.2, random_state=42)

y_train = to_categorical(y_train)
y_test = to_categorical(y_test)

vocab_size = 3000
max_length = 200
oov_token = "<OOV>"

tokenizer = Tokenizer(num_words=vocab_size, oov_token=oov_token)
tokenizer.fit_on_texts(X_train)

X_train_seq = tokenizer.texts_to_sequences(X_train)
X_test_seq = tokenizer.texts_to_sequences(X_test)

X_train_pad = pad_sequences(X_train_seq, maxlen=max_length, padding='post', truncating='post')
X_test_pad = pad_sequences(X_test_seq, maxlen=max_length, padding='post', truncating='post')

model = Sequential([
    Embedding(vocab_size, 64, input_length=max_length),
    Bidirectional(LSTM(32, return_sequences=True)),
    GlobalMaxPooling1D(),
    Dense(16, activation='relu'),
    Dense(32, activation='relu'),
    Dropout(0.2),
    Dense(2, activation='softmax')
])


model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X_train_pad, y_train, epochs=5, validation_data=(X_test_pad, y_test))

loss, acc = model.evaluate(X_test_pad, y_test)
print(f"Test accuracy: {acc:.2f}")

model.save('spam_classification_model1.keras')
import pickle
with open('tokenizer1.pkl', 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)