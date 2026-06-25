# Added Tenant Affordability + Chat Features

This revised package adds:

1. Tenant-landlord chat after application acceptance only.
2. Tenant application salary field for AI rental sustainability prediction.
3. Employment information: Full time, Part time, Self employed, Unemployed, Student.
4. Household information: number of dependents and household notes.
5. Current rental information: current monthly rent paid, if currently renting.
6. CSV dataset: `data/tenant_affordability_dataset.csv`.
7. SQL migration: `database/tenant_affordability_chat_migration.sql`.

Main file revised: `main.py`.

To run normally:

```bash
streamlit run main.py
```

If your database already exists, run the SQL migration file once. The app also tries to add missing columns automatically when it starts.
