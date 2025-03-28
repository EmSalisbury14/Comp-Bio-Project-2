# %%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# %%
# Load the CDD data
cdd_file = "cddid.tbl.gz"
cdd_df = pd.read_csv(cdd_file, sep="\t", header=None, names=["CDD_ID", "Domain_ID", "Gene_Name", "Description", "Length"])
cdd_df = cdd_df[["Domain_ID","Gene_Name"]]
# View first few rows
print(cdd_df)


# %%
superfam_df = pd.read_csv("CDDID_SuperfamilyID.txt", sep='\t')
superfam_df.columns = ["CDD_ID_1", "Accession_1", "CDD_ID_2", "Accession_2"]

superfam_df = superfam_df.drop(columns=[ "Accession_1","Accession_2" ])
# Rename columns for clarity
superfam_df.columns = ["CDD_ID", "Superfamily"]

# Drop duplicates if any
superfam_df = superfam_df.drop_duplicates()
#superfam_df

# %%
RNA_seq_df = pd.read_csv("amphimedon_rnaseq.txt", sep='\t')
#RNA_seq_df.head(1)

# %%
cddid_df = pd.read_csv("mart_export (2).txt", sep='/t')
cddid_df.head(1)
cddid_df[['Gene_ID', 'CDD_ID']] = cddid_df["Gene stable ID	CDD ID"].str.split("\t", expand=True)
# Drop the old combined column
cddid_df = cddid_df.drop(columns=["Gene stable ID	CDD ID"])
#cddid_df

# %% [markdown]
# Uploading all the files, melting the superfamily one to get it workable columns. as well as seperating the Gene ID and CDD id columns in the other file

# %%
"""print("cddid_df columns:", cddid_df.columns)
print("superfam_df columns:", superfam_df.columns)
print("RNA_seq_df columns:", RNA_seq_df.columns)
print(cddid_df.head(5))
superfam_df"""

# %% [markdown]
# merging the two dataframes based on the CDD id, however getting lost here as we are losing the superfamily data and getting NaN, unsure how to fix

# %% [markdown]
# 

# %%
merged_df = cddid_df.merge(superfam_df, on='CDD_ID')
df_merged = merged_df.merge(cdd_df, left_on="Superfamily", right_on="Domain_ID", how="left")

# Append gene names directly to the Superfamily column
df_merged["Superfamily"] = df_merged["Superfamily"] + ": " + df_merged["Gene_Name"]

df_merged.drop(columns=["Domain_ID"], inplace=True)
merged_df=df_merged
df_merged

# %% [markdown]
# Merging with the RNA seq data to get a table

# %%
final_df = merged_df.merge(RNA_seq_df, left_on="Gene_ID", right_on="GeneID", how="inner")
final_df["CDD_ID"]

final_df

# %% [markdown]
# Check if same gene ID, then sum TPM value

# %%
#Drop unnecessary columns
Superfamily_Transcript_df =  final_df.drop(columns=['GeneID','CDD_ID','Gene_ID'])

#print(Superfamily_Transcript_df)

#Keep all unique superfamily-transcript ID combinations
df_unique = Superfamily_Transcript_df.drop_duplicates(subset=["Superfamily", "TranscriptID"])
#df_unique.drop(columns=["TranscriptID"], inplace=True)
#print(df_unique)

# Sum TPM across all rows with the same Superfamily
#df_summed = df_unique.groupby("Superfamily").sum(numeric_only=True).reset_index()
df_summed = df_unique.groupby("Superfamily").agg({
    "Gene_Name": "first",  # Keeps one representative Gene_Name per Superfamily
    **{col: "sum" for col in df_unique.columns if col not in ["Superfamily", "Gene_Name"]}
}).reset_index()
print(df_summed) 

#print(df_summed)

numeric_cols = df_summed.columns[3:]  # Select only numerical columns
#df_loged = df_summed[numeric_cols]
df_loged = np.log2(df_summed[numeric_cols].replace(0, 0.5) + 0.5)
df_loged["Superfamily"] = df_summed["Superfamily"]
df_loged["Gene_Name"] = df_summed["Gene_Name"]
df_loged = df_loged.sort_values(by="Gene_Name", ascending=True)
df_loged.drop(columns=["Gene_Name"] ,inplace= True)


df_loged


# %%
'''result_df= aggregate_duplicates(gene_TPM_df)'''
output_file = 'unique_TPM_expression_amph.txt'
df_loged.to_csv(output_file, sep='\t', index=False)
df_loged

# %% [markdown]
# code for plottingg

# %%
df_heat = df_summed.loc[:, df_summed.columns.str.startswith("Sample")]

df_heat.head()

# %% [markdown]
# mean centered

# %%
row_mean = df_heat.mean(axis=1)
log_mean = np.log2(row_mean)
log_mean

# %%
numeric_cols = df_loged.select_dtypes(include='number')
df_centered = numeric_cols.sub(log_mean, axis=0)
df_centered.head()

# %%
max_value = df_centered.max().max()

min_value = df_centered.min().min()

print("Max value:", max_value)
print("Min value:", min_value)

# %% [markdown]
# row cluster

# %% [markdown]
# plotting the heatmap

# %%
import matplotlib.colors as mcolors

# %%
plt.figure(figsize=(12, 6))
normalize = mcolors.TwoSlopeNorm(vcenter=0, vmin=-5, vmax=5)
ax = plt.gca()

sns.heatmap(df_centered, cmap="RdBu_r", norm = normalize)
plt.xlabel("Stage Points")
ax.xaxis.set_label_coords(0.5, -0.25)
plt.ylabel("Superfamily")
plt.title("All Superfamily Domain Prevalence Over Embryonic Stage Development")
plt.xticks(rotation=45)
plt.legend(title="Fig. project 1 part 2.The superfamily domains have been transformed to log2 TPM values.\nTheir prevalence is centered on the row mean.",
           loc='upper center',
           bbox_to_anchor=(0.5, -0.36),
           ncol = 20)
plt.yticks([])
plt.show()

# %% [markdown]
# code for mapping smaller heatmap

# %%
#Smaller Heatmap
tpm_columns = [col for col in df_summed.columns if col.startswith('Sample.')]
df_summed['Max_Fold_Change'] = df_summed[tpm_columns].max(axis=1) / (df_summed[tpm_columns].min(axis=1) + 0.5)

#sort based on df_summed["Max_Fold_Change"]
df_sortMX = df_summed.sort_values(by='Max_Fold_Change', ascending=False)

gene_counts = final_df[final_df[tpm_columns].gt(1).all(axis=1)].groupby('Superfamily').size().reset_index(name='Gene_Count')
gene_counts = gene_counts[gene_counts['Gene_Count'] > 0]
#merge gene counts
df_summed_W_genecount = df_sortMX.merge(gene_counts, on='Superfamily', how='left')
#drop na
df_summed_W_genecount = df_summed_W_genecount.dropna(subset=['Gene_Count']) 


top_20_superfamilies = df_summed_W_genecount.head(20)

heatmap_data = top_20_superfamilies.set_index('Superfamily')[tpm_columns]

heatmap_data_log2 = np.log2(heatmap_data + 0.5)

row_mean = heatmap_data_log2.mean(axis=1)
heatmap_data_centered = heatmap_data_log2.sub(row_mean, axis=0)

heatmap_data_centered["log2_diff"] = heatmap_data_log2["Sample.00h"] - heatmap_data_log2["Sample.16h"]
heatmap_data_sorted = heatmap_data_centered.sort_values(by="log2_diff", ascending=False)
heatmap_data_sorted = heatmap_data_sorted.drop("log2_diff", axis=1)

row_labels = [f"{superfamily} ({count} genes)" for superfamily, count in zip(top_20_superfamilies['Superfamily'], top_20_superfamilies['Gene_Count'])]

# Plot the smaller heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(
    heatmap_data_sorted,
    cmap="RdBu_r",
    yticklabels=row_labels,
    vmin=-7,
    vmax=7,
)
plt.title('Top 20 Superfamilies of Drosophila by Max Fold Change in Log2 TPM')
plt.xlabel('Stage Points')
plt.ylabel('Superfamily (Number of Genes with >1 TPM)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.draw()
plt.show()
plt.savefig('Top Domains Heatmap- drosophila.pdf')



