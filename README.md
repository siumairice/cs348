# CS348 Project

## Prerequisites
- Docker Desktop

## How to Run the Application

### 1. Start the Containers
Open your terminal in the root directory of this project and execute the following command:

```bash
docker compose up --build
```
### 2. Verify the Output

```text
cs348-lego-app  | Waiting 10 seconds for the database to boot...
cs348-lego-app  | Successfully connected to the database!
cs348-lego-app  | 
cs348-lego-app  |             SELECT s.set_num, s.name AS set_name, s.year, t.name AS theme_name
cs348-lego-app  |             FROM sets s
cs348-lego-app  |             INNER JOIN themes t ON s.theme_id = t.id
cs348-lego-app  |             ORDER BY s.year DESC
cs348-lego-app  |         
cs348-lego-app  | [10316-1] The Lord of the Rings: Rivendell (2023) - Theme: Icons
cs348-lego-app  | [75355-1] X-Wing Starfighter (2023) - Theme: Star Wars
cs348-lego-app  | [75192-1] Millennium Falcon (2017) - Theme: Star Wars
cs348-lego-app  | 
cs348-lego-app  | MySQL connection is closed.
cs348-lego-app  | 
cs348-lego-app exited with code 0
```

### 3. Exit the app
Exit the app via:
```bash
docker compose down -v
```
or Ctrl + C
