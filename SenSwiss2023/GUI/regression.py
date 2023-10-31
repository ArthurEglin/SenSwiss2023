#shift_min_gfapToSTOP = [2.366340191925019, 1.8150536114669649, 1.9651148089914159]
#shift_cen_gfapToSTOP = [0.5867143094193352, 0.5389107121690131, 0.6300544523907092]
#shift_min_gfapToSTOP = [2.366340191925019, 1.8150536114669649]
#shift_cen_gfapToSTOP = [0.5867143094193352, 0.5389107121690131]
import numpy as np
import sklearn.linear_model as lm

model_min_gfapToSTOP = lm.LinearRegression()
model_cen_gfapToSTOP = lm.LinearRegression()
model_min_aunpToSTOP = lm.LinearRegression()
model_cen_aunpToSTOP = lm.LinearRegression()
model_min_2 = lm.LinearRegression()
model_cen_2 = lm.LinearRegression()

# Data for training
# gfapToStop
shift_min_gfapToSTOP = [2.366340191925019, 1.8150536114669649]
shift_cen_gfapToSTOP = [0.5867143094193352, 0.5389107121690131]

# AuNp to Stop
shift_min_aunpToSTOP = [1.525055915100893, 1.5228791335606502]
shift_cen_aunpToSTOP = [0.375969662640955, 0.4122935461191446]

shift_min_gfapAUNP = [1.5250559151010066, 1.5228791335603091]
shift_cen_gfapAUNP = [0.3759696626408413, 0.4122935461190309]

# Original concentration : 8ng/mL 3,456mg/mL 0,216mg/mL
# After dilution : 1.33, 0.576, 0.036
concentrations_train = [1333, 576]

# Data to test
test_min_gfapToStop = [0.8777267456115396]
test_cen_aunpToStop = [0.16981979248930656]
test_min_aunpToStop = [0.3497073309551979]
test_cen_aunpToStop = [0.03600144771405667]
test_min_2 = [1.7562695651356535]
test_cen_2 = [0.2948395]

# Fit a linear model to the data
model_min_gfapToSTOP.fit(np.array(shift_min_gfapToSTOP).reshape(-1, 1), concentrations_train)
model_cen_gfapToSTOP.fit(np.array(shift_cen_gfapToSTOP).reshape(-1, 1), concentrations_train)

model_cen_aunpToSTOP.fit(np.array(shift_cen_aunpToSTOP).reshape(-1, 1), concentrations_train)
model_min_aunpToSTOP.fit(np.array(shift_min_aunpToSTOP).reshape(-1, 1), concentrations_train)

model_cen_2.fit(np.array(shift_cen_gfapAUNP).reshape(-1, 1), concentrations_train)
model_min_2.fit(np.array(shift_min_gfapAUNP).reshape(-1, 1), concentrations_train)

# If there are values to predict, use the model to predict them
dilution_ratio = 6

if len(test_min_gfapToStop) > 0:
    print("Prediction using min wave GFAP to STOP: ", dilution_ratio*model_min_gfapToSTOP.predict(np.array(test_min_gfapToStop).reshape(-1, 1)))

if len(test_min_gfapToStop) > 0:
    print("Prediction using centroid GFAP to STOP: ", dilution_ratio*model_cen_gfapToSTOP.predict(np.array(test_cen_aunpToStop).reshape(-1, 1)))

if len(test_min_aunpToStop) > 0:
    print("Prediction using min wave AuNP to STOP: ", dilution_ratio*model_min_aunpToSTOP.predict(np.array(test_min_aunpToStop).reshape(-1, 1)))

if len(test_cen_aunpToStop) > 0:
    print("Prediction using centroid AuNP to STOP: ", dilution_ratio*model_cen_aunpToSTOP.predict(np.array(test_cen_aunpToStop).reshape(-1, 1)))

if len(test_min_2) > 0:
    print("Prediction using min wave GFAP to AuNP: ", dilution_ratio*model_min_2.predict(np.array(test_min_2).reshape(-1, 1)))

if len(test_cen_2) > 0:
    print("Prediction using centroid GFAP to AuNP: ", dilution_ratio*model_cen_2.predict(np.array(test_cen_2).reshape(-1, 1)))


# Plot the fit
"""
import matplotlib.pyplot as plt

plt.scatter(shift_min_gfapToSTOP, concentrations_train, color="black", label="min")
plt.plot(shift_min_gfapToSTOP, model_min_gfapToSTOP.predict(np.array(shift_min_gfapToSTOP).reshape(-1, 1)), color="blue", label="min fit")
plt.scatter(shift_cen_gfapToSTOP, concentrations_train, color="red", label="cen")
plt.plot(shift_cen_gfapToSTOP, model_cen_gfapToSTOP.predict(np.array(shift_cen_gfapToSTOP).reshape(-1, 1)), color="green", label="cen fit")
plt.legend()
plt.show()

"""