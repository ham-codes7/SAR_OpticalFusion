"""Demo presets (never used for training) and the regions the models learn from."""

# Dry-season windows keep optical cloud-free for training; labels span 2018 -> 2023.
BEFORE = ("2017-12-01", "2018-02-28")
AFTER = ("2023-12-01", "2024-02-29")

PRESETS = [
    {
        "id": "bengaluru-north",
        "name": "North Bengaluru",
        "place": "Devanahalli corridor, Karnataka",
        "phenomenon": "urban",
        "bbox": [77.60, 13.14, 77.76, 13.26],
        "blurb": "Farmland turning into layouts and tech parks along the airport corridor.",
    },
    {
        "id": "hyderabad-west",
        "name": "West Hyderabad",
        "place": "Financial District, Telangana",
        "phenomenon": "urban",
        "bbox": [78.24, 17.36, 78.40, 17.48],
        "blurb": "One of India's fastest-growing office and housing clusters.",
    },
    {
        "id": "mizoram-hills",
        "name": "Mizoram hills",
        "place": "Near Aizawl, Mizoram",
        "phenomenon": "deforestation",
        "bbox": [92.80, 23.55, 92.96, 23.67],
        "blurb": "Hill forest cleared in patches; under cloud for much of the monsoon.",
    },
    {
        "id": "karbi-anglong",
        "name": "Karbi Anglong",
        "place": "Assam",
        "phenomenon": "deforestation",
        "bbox": [93.30, 26.00, 93.46, 26.12],
        "blurb": "Forest edge under pressure from clearing and encroachment.",
    },
]

TRAINING = {
    "urban": [
        [73.68, 18.54, 73.84, 18.66],  # Pune west
        [80.14, 12.78, 80.28, 12.92],  # Chennai south
        [72.42, 22.98, 72.58, 23.10],  # Ahmedabad west
        [76.94, 28.38, 77.10, 28.50],  # Gurugram
        [77.62, 12.80, 77.78, 12.92],  # Bengaluru south-east
        [78.44, 17.20, 78.60, 17.32],  # Hyderabad south
        [77.40, 28.42, 77.56, 28.54],  # Greater Noida
        [88.42, 22.52, 88.58, 22.64],  # Kolkata, New Town
        [75.74, 26.76, 75.90, 26.88],  # Jaipur south
        [80.92, 26.74, 81.08, 26.86],  # Lucknow south-east
    ],
    "deforestation": [
        [92.60, 23.90, 92.76, 24.02],  # Mizoram north
        [93.00, 23.20, 93.16, 23.32],  # Mizoram south-east
        [94.30, 26.00, 94.46, 26.12],  # Nagaland
        [90.30, 25.50, 90.46, 25.62],  # Meghalaya, Garo hills
        [93.60, 24.40, 93.76, 24.52],  # Manipur
        [92.90, 25.20, 93.06, 25.32],  # Dima Hasao, Assam
        [91.80, 23.90, 91.96, 24.02],  # Tripura north
        [95.80, 27.30, 95.96, 27.42],  # Arunachal, Changlang foothills
        [92.40, 23.80, 92.56, 23.92],  # Mizoram west, Mamit
        [93.40, 24.90, 93.56, 25.02],  # Manipur, Tamenglong
    ],
}
