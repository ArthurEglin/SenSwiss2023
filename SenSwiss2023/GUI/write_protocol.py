
import pandas as pd

# Define your own data
data = {
    "port": [1, 2, 3, 4, 5],  # Replace with your port values
    "action": ["start", "stop", "start", "start", "stop"],  # Replace with your action values
    "volume": [0.25, 0.5, 0.75, 1.0, 0.1],  # Replace with your volume values
    "speed": [1.5, 0.8, 2.0, 1.2, 0.5],  # Replace with your speed values
    "title": ["title1", "title2", "GFAP", "title4", "title5"]  # Replace with your title values
}

# Create a DataFrame
df = pd.DataFrame(data)

# Append a new row
df = pd.concat([df, pd.DataFrame([[6, "start", 0.5, 1.0, "title6"]], columns=df.columns)], ignore_index=True)

# Display title one by one
def display_title(title):
    print(title)

row_index = 0
while row_index < len(df):
    display_title(df.iloc[row_index]["title"])
    row_index += 1