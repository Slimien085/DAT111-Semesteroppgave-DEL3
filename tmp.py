from Foreles4_0_Imports import *
solgtLeil = [
    [80,    3.4,    8.2], # m2, Standard, Pris
    [108,   3.4,    9.4],
    [77,    1.5,    5.3],
    [135,   2.5,    9.3],
    [45,    3.1,    5.2]]
df = pd.DataFrame(columns=["m2","Std", "Price"], data=solgtLeil)
X = df[['m2','Std']]
y = df['Price']
model = LinearRegression()
model.fit(X, y)
estLeil = [[100,2],[120,4], [220,1], [200,4], [50,4]]
dfTest = pd.DataFrame(columns=["m2","Std"], data=estLeil) # dfTest = f(estLeig)
dfTest["Est"] = model.predict(dfTest).astype(int)
dfTest["Price"] = df["Price"]
print("Leiligheter i Bergen sentrum Standard(4=best) ")
print(dfTest)







