import pandas as pd

test_file = r"C:\Users\HARSH\OneDrive\Desktop\Homonculus15\Projects\Network Security\valid_data\test.csv"

df = pd.read_csv(test_file)

# Remove target column
df = df.drop(columns=["Result"])

output_file = r"C:\Users\HARSH\OneDrive\Desktop\Homonculus15\Projects\Network Security\valid_data\prediction_test\prediction_test.csv"

df.to_csv(output_file, index=False)

print("Prediction file created successfully!")
print("Saved at:", output_file)
print("Shape:", df.shape)