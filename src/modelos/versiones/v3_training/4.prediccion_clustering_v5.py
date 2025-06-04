import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import joblib

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report

# === CARGA DE DATOS ===
df = pd.read_csv("stats/dataset_modelo_clusterizado.csv", parse_dates=["FECHA_EVENTO"])

# === VARIABLES ===
features = ['COSTE_ESTIMADO', 'SEMANA', 'DIA_SEMANA', 'MES', 'TIPO_EVENTO', 'COMUNIDAD']
target = 'CLUSTER_EVENTO'

X = df[features]
y = df[target]

# === PREPROCESAMIENTO ===
numeric_features = ['COSTE_ESTIMADO', 'SEMANA']
categorical_features = ['DIA_SEMANA', 'MES', 'TIPO_EVENTO', 'COMUNIDAD']

numeric_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(drop='first', sparse_output=False))
])

preprocessor = ColumnTransformer([
    ('num', numeric_pipeline, numeric_features),
    ('cat', categorical_pipeline, categorical_features)
])

pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', RandomForestClassifier(random_state=42))
])

# === BÚSQUEDA DE HIPERPARÁMETROS ===
param_grid = {
    'model__n_estimators': [50, 100],
    'model__max_depth': [None, 10]
}

grid_search = GridSearchCV(pipeline, param_grid, cv=3, scoring='accuracy', verbose=1, n_jobs=-1)
grid_search.fit(X, y)

# === MEJOR MODELO ===
best_model = grid_search.best_estimator_
print("\n🌟 Mejores hiperparámetros:")
print(grid_search.best_params_)

# === EVALUACIÓN ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
best_model.fit(X_train, y_train)
y_pred = best_model.predict(X_test)

print("\n📊 Evaluación del modelo de predicción de clúster:")
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))

# === MATRIZ DE CONFUSIÓN GRAFICADA ===
plt.figure(figsize=(8, 6))
sns.heatmap(confusion_matrix(y_test, y_pred), annot=True, fmt='d', cmap='Blues')
plt.title("📊 Matriz de Confusión - Predicción de Clúster")
plt.xlabel("Predicción")
plt.ylabel("Real")
plt.tight_layout()
plt.show()

# === GUARDAR MODELO ENTRENADO ===
output_path = "src/modelos"
os.makedirs(output_path, exist_ok=True)
joblib.dump(best_model, os.path.join(output_path, "modelo_predictor_cluster_v1.pkl"))
print(f"\n✅ Modelo guardado como '{output_path}/modelo_predictor_cluster_v1.pkl'")