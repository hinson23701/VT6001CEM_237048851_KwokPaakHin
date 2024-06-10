import librosa
import mysql.connector
import numpy as np
from flask import Flask, redirect, url_for, request, flash,render_template, session
from tensorflow import keras
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
model = keras.models.load_model('song_genreModel.h5')
model2 = keras.models.load_model('SingerModel.h5')

# remote database Connection configuration
config = {
    
    'user': 'freedb_music_admin',
    'password': 'cs2Yugp&!dBydDN',
    'host': 'sql.freedb.tech',
    'database': 'freedb_music_genre',
    'raise_on_warnings': True
}

def preprocess_audio(file_path):
    audio, sr = librosa.load(file_path, duration=None)
    spectrogram = librosa.feature.melspectrogram(y=audio, sr=sr)
    spectrogram = librosa.power_to_db(spectrogram)
    desired_shape = (26)
    spectrogram = np.resize(spectrogram, desired_shape)
    spectrogram = np.expand_dims(spectrogram, axis=0)
    return spectrogram


@app.route('/', methods=['GET', 'POST'])
    
def predict_genre():

    session.get('user_id')
    user_id = session.get('user_id')
    if request.method == 'POST':
        file = request.files['file']
        file_path = 'temp.wav'
        file.save(file_path)

        preprocessed_audio = preprocess_audio(file_path)

        predictions = model.predict(preprocessed_audio)
        predicted_class = np.argmax(predictions)

        class_to_genre = {
            0: 'Blues',
            1: 'Classical',
            2: 'Disco',
            3: 'Hip Hop',
            4: 'Jazz',
            5: 'Metal',
            6: 'Reggae',
            7: 'Country',
            8: 'Classical',
            9: 'Rock'
        }

        predicted_genre = class_to_genre[predicted_class]

        try:
            # Establish a connection to the MySQL database
            conn = mysql.connector.connect(**config)

            if conn.is_connected():
                # Create a cursor object to execute SQL queries
                cursor = conn.cursor()

                # Execute the SQL query
                query = "SELECT * FROM music WHERE genre = '" + predicted_genre + "'"
                cursor.execute(query)

                # Fetch all the rows returned by the query
                rows = cursor.fetchall()

                # Insert the predicted song into the `favourite_usersong` table
               
                for row in rows:
                    song_link = row[3]  # assuming the song ID is the first column in the `music` table
                    query = "INSERT INTO predict_records (user_id, song_link) VALUES (%s, %s)"
                    cursor.execute(query, (user_id, song_link))
                conn.commit()


                # Close the cursor and the database connection
                cursor.close()
                conn.close()

                return render_template('result.html', genre=predicted_genre, rows=rows)

        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")

    return render_template('upload.html')
          
@app.route("/home")

def home():
  return render_template("index.html")




@app.route('/Singer', methods=['GET', 'POST'])


def predict_singer():
    session.get('user_id')
    user_id = session.get('user_id')
    if request.method == 'POST':
        # Get the uploaded file
        file = request.files['audio']

        # Save the uploaded file
        file_path = 'uploaded_audio.wav'  # Specify the path to save the uploaded file
        file.save(file_path)

        # Preprocess the audio file
        preprocessed_audio = preprocess_audio(file_path)

        # Make predictions
        predictions = model2.predict(preprocessed_audio)
        predicted_class = np.argmax(predictions)

        # Define the mapping from class index to singer labels
        class_to_singer = {
            0: 'Crystal Cheung',
            1: 'Fiona Fung',
            2: 'Hins Cheung',
            3: 'Jason Chan'
        }

        # Get the predicted singer label
        predicted_singer = class_to_singer[predicted_class]

        try:
            # Establish a connection to the MySQL database
            conn = mysql.connector.connect(**config)

            if conn.is_connected():
                # Create a cursor object to execute SQL queries
                cursor = conn.cursor()

                # Execute the SQL query
                query = "SELECT * FROM singer WHERE genre = '" + predicted_singer + "'"
                cursor.execute(query)

                # Fetch all the rows returned by the query
                rows = cursor.fetchall()

                for row in rows:
                    song_link = row[3]  # assuming the song ID is the first column in the `music` table
                    query = "INSERT INTO predict_records (user_id, song_link) VALUES (%s, %s)"
                    cursor.execute(query, (user_id, song_link))
                conn.commit()

                # Close the cursor and the database connection
                cursor.close()
                conn.close()

            return render_template('result2.html', predicted_singer = predicted_singer, rows=rows)

        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")

    return render_template('SingerClassify.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Establish a connection to the MySQL database
            conn = mysql.connector.connect(**config)

            if conn.is_connected():
                # Create a cursor object to execute SQL queries
                cursor = conn.cursor()

                # Check if the user exists in the database
                cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
                user = cursor.fetchone()

                if user and user[2] == password:
                    # Store the user information in the session
                    session['user_id'] = user[0]
                    
                    return redirect(url_for('home'))
                else:
                    flash('Invalid email or password', 'danger')

                # Close the cursor and the database connection
                cursor.close()
                conn.close()

        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            # Establish a connection to the MySQL database
            conn = mysql.connector.connect(**config)

            if conn.is_connected():
                # Create a cursor object to execute SQL queries
                cursor = conn.cursor()

                # Check if the email already exists in the database
                cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash('Email already registered', 'danger')
                else:
                    # Insert the new user into the database
                    cursor.execute(
                    "INSERT INTO user (username, password, email) VALUES (%s, %s, %s)",
                    (username, password, email)
                    )
                    conn.commit()
                    flash('Registration successful! You can now log in.', 'success')
                    return redirect(url_for('login'))

                # Close the cursor and the database connection
                cursor.close()
                conn.close()

        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")

    return render_template('register.html')

@app.route('/profile')

def profile():
    session.get('user_id')
    user_id = session.get('user_id')
    if user_id == "":
        return redirect(url_for('login'))

 
    try:
            # Establish a connection to the MySQL database
            conn = mysql.connector.connect(**config)

            if conn.is_connected():
                # Create a cursor object to execute SQL queries
                cursor = conn.cursor()

                # Execute the SQL query to fetch the user's predict_records
                query = "SELECT * FROM predict_records WHERE user_id = %s"
                cursor.execute(query, (user_id,))

                # Fetch all the rows returned by the query
                rows = cursor.fetchall()

                # Execute the SQL query to fetch the user's information
                
                query = "SELECT * FROM user WHERE id = %s"
                cursor.execute(query, (user_id,))

                # Fetch the user's information
                user = cursor.fetchone()

                # Close the cursor and the database connection
                cursor.close()
                conn.close()

                return render_template('profile.html', user=user, rows=rows)

    except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")

    





    



if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)