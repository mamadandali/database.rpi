import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# Create sample dataframe
data = {
    'weight': [100, 150, 120, 80],
    'damage': [5, 3, 4, 2],
    'temperature': [25, 30, 28, 22],
    'humidity': [60, 50, 55, 70],
    'food_type': ['cheese', 'peanut', 'cheese', 'meat'],
    'trapped': ['yes', 'no', 'yes', 'no']
}
df = pd.DataFrame(data)

# Encode categorical variables
le_food = LabelEncoder()
le_target = LabelEncoder()

df['food_type_encoded'] = le_food.fit_transform(df['food_type'])
df['trapped_encoded'] = le_target.fit_transform(df['trapped'])

# Define features and target
X = df[['weight', 'damage', 'temperature', 'humidity', 'food_type_encoded']]
y = df['trapped_encoded']

# Split data into train and test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train decision tree model
model = DecisionTreeClassifier()
model.fit(X_train, y_train)

# Food recommendation function
def recommend_food(weight, damage, temperature, humidity):
    possible_foods = le_food.classes_
    best_food = None
    highest_prob = 0

    for food in possible_foods:
        food_encoded = le_food.transform([food])[0]
        sample = [[weight, damage, temperature, humidity, food_encoded]]
        prob = model.predict_proba(sample)[0][1]  # Probability of 'yes' class
        if prob > highest_prob:
            highest_prob = prob
            best_food = food

    return best_food

# Example usage
print(recommend_food(130, 4, 27, 58))  # Output: 'cheese'
