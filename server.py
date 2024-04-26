from flask import Flask, request, jsonify
from bson import ObjectId  
from flask_cors import CORS
import pymongo
import bcrypt
import jwt
import datetime

app = Flask(__name__)
CORS(app, origins="*")

try:
    client = pymongo.MongoClient("mongodb+srv://arvind_varma:arvind_varma@cluster0.vn12nqf.mongodb.net/test?retryWrites=true&w=majority")
    print("Connected successfully!!!")
    db = client['Dashboard']
    dashboard = db['Dashboard']
    user = db['user']
    
except:
    print("Could not connect to MongoDB")


##############################################
# Create operation for multiple documents
@app.route('/api/data', methods=['POST'])
def create_data():
    data = request.json
    if isinstance(data, list):
        dashboard.insert_many(data)
        return jsonify({"message": "Data created successfully"})
    else:
        return jsonify({"error": "Invalid data format. Expected a list of documents."}), 400
####################################
# Read operation
@app.route('/api/data', methods=['GET'])
def get_all_data():
    data = list(dashboard.find({}, {'_id': 0}))
    return jsonify(data)


#####################################
#Read opreation 
@app.route('/api/chart', methods=['GET'])
def get_visualization_data():
    filters = {}
    end_year = request.args.get('end_year')
    if end_year:
        filters['end_year'] = int(end_year)
    
    topics = request.args.getlist('topics')
    if topics:
        filters['topic'] = {"$in": topics}
    
    region = request.args.get('region')
    if region:
        filters['region'] = region
    
    country = request.args.get('country')
    if country:
        filters['country'] = country
    
    source = request.args.get('source')
    if source:
        filters['source'] = source
  
    sector = request.args.get('sector')
    if sector:
        filters['sector'] = sector
    
    print("Filters:", filters)
    
    match_stage = {"$match": filters} if filters else {}
    if not match_stage:
     match_stage = {"$match": {}}
    pipeline = [
      match_stage,
        {
            "$group": {
                "_id": {
                    "country": "$country",
                    "intensity":{"$avg": "$intensity"},
                },
                
            }
        }
    ]
    data = list(dashboard.aggregate(pipeline))
    return jsonify(data)

#######################################
#user login and signup opreation 

@app.route('/api/signup', methods=['POST'])
def create_user():
    data = request.json
    existing_user = user.find_one({"email": data["email"]})
    if existing_user:
        return jsonify({"message": "User already exists"}), 409  # HTTP status code 409 for Conflict
    else:
        password = data["password"].encode('utf-8')  # Encode password to bytes
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt(14)).decode('utf-8')  # Hash and decode
        data["password"] = hashed_password
        new_user = user.insert_one(data)
        return jsonify({"message": "User created successfully",
                        "user": str(new_user)}), 201  # HTTP status code 201 for Created

#######################################
app.config['SECRET_KEY'] = 'vdggtgsddsdwrwgdfthtdbdgthw4'

# API endpoint for user login

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.json
    user_data = user.find_one({"email": auth["email"]})
    if user_data and bcrypt.checkpw(auth["password"].encode('utf-8'), user_data["password"].encode('utf-8')):
        token = jwt.encode({'email': auth['email'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)}, app.config['SECRET_KEY'])
        
        # Convert ObjectId to string for the _id field
        user_data['_id'] = str(user_data['_id'])
        
        # Convert the user_data dictionary to a list of tuples
        user_info = (user_data)
        
        # Return the JSON response
        return jsonify({'token': token, 'user': user_info}), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401


if __name__ == '__main__':
    app.run(port=8080,debug=True)

