from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Load the dataset (ensure this path is correct if you moved the file)

df=pd.read_csv(r"C:\Users\hanis\OneDrive\Desktop\Team Tubelight\Local-Artisian_AI\Artisans.csv")

# Identify numerical and categorical columns
numerical_features = df.select_dtypes(include=np.number).columns
categorical_features = df.select_dtypes(include='object').columns

# Create preprocessing pipelines for numerical and categorical features
numerical_transformer = StandardScaler()
categorical_transformer = OneHotEncoder(handle_unknown='ignore')

# Create a column transformer to apply different transformations to different columns
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_transformer, numerical_features),
        ('cat', categorical_transformer, categorical_features)])

# Apply preprocessing
df_processed = preprocessor.fit_transform(df)


# Determine the optimal number of clusters using the elbow method
wcss = []
for i in range(1, 11):
    kmeans = KMeans(n_clusters=i, init='k-means++', random_state=42, n_init=10)
    kmeans.fit(df_processed)
    wcss.append(kmeans.inertia_)

# Plot the elbow method graph
plt.figure(figsize=(8, 4))
plt.plot(range(1, 11), wcss)
plt.title('Elbow Method')
plt.xlabel('Number of clusters')
plt.ylabel('WCSS')
#plt.show()

from sklearn.cluster import KMeans

# Train the K-Means model with 4 clusters
kmeans_model = KMeans(n_clusters=4, init='k-means++', random_state=42, n_init=10)
kmeans_model.fit(df_processed)

# Add the cluster labels to the original DataFrame
df['cluster_label'] = kmeans_model.labels_

# Display the first few rows with the new cluster labels
print(df.head())

# Get the size of each cluster
cluster_sizes = df['cluster_label'].value_counts().sort_index()
print("Cluster Sizes:")
print(cluster_sizes)

# Analyze the mean of numerical features for each cluster
cluster_means = df.groupby('cluster_label')[numerical_features].mean()
print("\nMean of Numerical Features per Cluster:")
print(cluster_means)

# Analyze the distribution of categorical features per cluster
for feature in categorical_features:
    print(f"\nDistribution of '{feature}' per Cluster:")
    print(df.groupby('cluster_label')[feature].value_counts(normalize=True).unstack().fillna(0))