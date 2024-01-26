# FastAPI User Management backend app.

## Get started with the following command:
`git clone https://github.com/tanuj-ralli/user-management.git`

### Pre-requisite 
1) Docker Desktop  

### Common Docker Commands:
```
To generate docker image: "docker-compose build"  
To run containers from docker image: "docker-compose up -d"
To see the logs of docker container: "docker logs -f user_management_application"
```

### About APIs
For user, register, login, view and update APIs are present.  
Username and password are required for login.

Once docker container is up,
Apis can be accessed at swagger url: [localhost:9999/docs](http://localhost:9999/docs)

### About Database Schema
Postgres Database is used to support the data storage.  
Following show the available tables:  

Table User:  
    id = Int(PK)  
    username = Str  
    first_name = Str  
    last_name = Str  
    hashed_password = Str  
    dob = DateTime  
    phone_number = Str  
    created_at = DateTime  
    updated_at = DateTime  
    is_active = Boolean(default=True)  
    is_deleted = Boolean(default=False)
