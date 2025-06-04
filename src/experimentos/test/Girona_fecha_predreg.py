import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from datetime import timedelta
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns

# === CARGA DE DATOS REALES Y DE PAGO ===
base_dir = os.path.dirname(os.path.abspath(__file__))
ruta_real = os.path.join(base_dir, '..', '..', 'data', 'clean', 'dataset_modelo.csv')
df = pd.read_csv(ruta_real)
df['FECHA_EVENTO'] = pd.to_datetime(df['FECHA_EVENTO'])
df = df[df['EVENTO_GRATUITO'] == 0]  # solo eventos de pago

# === ORDEN Y TARGET ===
df = df.sort_values('FECHA_EVENTO')
df['DIAS_HASTA_SIGUIENTE_EVENTO'] = df['FECHA_EVENTO'].shift(-1) - df['FECHA_EVENTO']
df['DIAS_HASTA_SIGUIENTE_EVENTO'] = df['DIAS_HASTA_SIGUIENTE_EVENTO'].dt.days

# Eliminar último evento sin siguiente
df = df.dropna(subset=['DIAS_HASTA_SIGUIENTE_EVENTO'])

# === NUEVAS VARIABLES TEMPORALES SIMPLES ===
df['DIA_SEMANA_NUM'] = df['FECHA_EVENTO'].dt.weekday

features = ['MES', 'DIA_SEMANA_NUM']
X = df[features]
y = df['DIAS_HASTA_SIGUIENTE_EVENTO']

# === ENTRENAMIENTO ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# === EVALUACIÓN ===
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"MAE del modelo: {mae:.2f} días")
print(f"MSE del modelo: {mse:.2f}")
print(f"R^2 del modelo: {r2:.2f}")

# === GRÁFICOS DE ERROR ===
plt.figure(figsize=(10, 6))
sns.scatterplot(x=y_test, y=y_pred)
plt.plot([y.min(), y.max()], [y.min(), y.max()], '--r')
plt.xlabel('Valores Reales')
plt.ylabel('Predicciones')
plt.title('Predicción vs Realidad (modelo temporal simple)')
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 6))
sns.histplot(y_test - y_pred, bins=20, kde=True)
plt.title('Distribución de errores (reales - predichos)')
plt.xlabel('Error')
plt.grid(True)
plt.tight_layout()
plt.show()

# === GUARDAR MODELO ===
joblib.dump(model, 'modelo_temporal_simple.pkl')

# === PREDICCIÓN DE DÍAS CON EVENTO NUEVO ===
def predecir_dias_siguiente_evento_simples(mes, dia_semana):
    df_nuevo = pd.DataFrame([{ 'MES': mes, 'DIA_SEMANA_NUM': dia_semana }])
    pred = model.predict(df_nuevo)[0]
    return int(round(pred))

# === AJUSTAR FECHA A DOMINGO ===
def ajustar_a_domingo(fecha):
    while fecha.weekday() != 6:
        fecha += timedelta(days=1)
    return fecha

# === USO DE EJEMPLO ===
if __name__ == '__main__':
    fecha_ultimo_evento = pd.to_datetime('2025-06-02')
    mes = fecha_ultimo_evento.month
    dia_semana = fecha_ultimo_evento.weekday()
    dias_estimados = predecir_dias_siguiente_evento_simples(mes, dia_semana)
    print(f"Días estimados hasta el próximo evento: {dias_estimados}")
    fecha_estimacion = fecha_ultimo_evento + timedelta(days=dias_estimados)
    fecha_domingo = ajustar_a_domingo(fecha_estimacion)
    print(f"Fecha sugerida (ajustada a domingo): {fecha_domingo.strftime('%Y-%m-%d')}")
