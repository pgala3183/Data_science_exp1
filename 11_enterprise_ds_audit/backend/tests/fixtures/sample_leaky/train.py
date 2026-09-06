# Intentionally leaky / incomplete sample for unit tests
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

df = pd.read_csv("data.csv")
X = df.drop("label", axis=1)
y = df["label"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # leakage: fit before split

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)

model = RandomForestClassifier(n_estimators=100)  # missing random_state
model.fit(X_train, y_train)
print(model.score(X_test, y_test))
