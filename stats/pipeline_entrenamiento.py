import pandas as pd
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class DataFrameSelector(BaseEstimator, TransformerMixin):
    def __init__(self, attribute_names):
        self.attribute_names = attribute_names

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.attribute_names]

    def get_feature_names_out(self, input_features=None):
        return self.attribute_names

def pipeline_dataset(df_real: pd.DataFrame, df_fake: pd.DataFrame) -> pd.DataFrame:
    df_real = df_real.copy()
    df_fake = df_fake.copy()
    df_real["REAL"] = 1
    df_fake["REAL"] = 0

    df = pd.concat([df_real, df_fake], ignore_index=True)

    df["EVENTO_GRATUITO"] = (df["TOTAL_RECAUDADO"] > 0).astype(int)
    df = df[df["EVENTO_GRATUITO"] == 1].copy()

    df.drop(columns=["NOMBRE_EVENTO", "NUM_INSCRITAS", "FECHA_EVENTO"], inplace=True, errors='ignore')

    numeric_features = ['NUM_PAGOS', 'TOTAL_RECAUDADO', 'COSTE_ESTIMADO', 'BENEFICIO_ESTIMADO', 'SEMANA']
    categorical_features = ['COMUNIDAD', 'DIA_SEMANA', 'MES', 'TIPO_EVENTO']

    numeric_pipeline = Pipeline([
        ('selector', DataFrameSelector(numeric_features)),
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', MinMaxScaler())
    ])

    categorical_pipeline = Pipeline([
        ('selector', DataFrameSelector(categorical_features)),
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(drop='first', sparse_output=False, dtype=int))
    ])

    full_pipeline = ColumnTransformer([
        ('num', numeric_pipeline, numeric_features),
        ('cat', categorical_pipeline, categorical_features)
    ])

    df_transformed = full_pipeline.fit_transform(df)
    feature_names = full_pipeline.get_feature_names_out()
    df_transformed = pd.DataFrame(df_transformed, columns=feature_names, index=df.index)

    columnas_extra = ['REAL', 'EVENTO_GRATUITO', 'NUM_ASISTENCIAS']
    columnas_extra = [col for col in columnas_extra if col in df.columns]
    df_extra = df[columnas_extra].reset_index(drop=True)

    df_final = pd.concat([df_transformed.reset_index(drop=True), df_extra], axis=1)

    return df_final
