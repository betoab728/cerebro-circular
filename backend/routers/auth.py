    # Check if user already exists
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, full_name=user.full_name, hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session)
):
    # PRIORITIZE MANUAL USER TABLE (Fix for missing User table schema)
    
    # Input Sanitization
    username_input = form_data.username.strip()
    password_input = form_data.password.strip()
    
    print(f"Login Attempt: Username='{username_input}'")
    
    statement = select(Usuario).where(Usuario.nombre == username_input)
    try:
        user_usuario = session.exec(statement).first()
        print(f"User Query Result: {user_usuario}")
    except Exception as e:
        print(f"Query Error: {e}")
        user_usuario = None
    
    if user_usuario:
        print(f"User Found. Verifying password...")
        # Check plain text password (as requested)
        if password_input != user_usuario.clave:
                print(f"Password Mismatch. Input='{password_input}', Stored='{user_usuario.clave}'")
                raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token for manual user
        print("Password Match. Generating token.")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_usuario.nombre, "role": "admin"}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        print("User NOT found in manual 'usuarios' table.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: Annotated[User | Usuario, Depends(get_current_user)]):
    # Adapt Usuario to UserRead schema if necessary
    if isinstance(current_user, Usuario):
        return UserRead(
            email=current_user.nombre,
            full_name=current_user.nombre,
            role="admin", # Default role for manual users
            is_active=True,
            id=current_user.id
        )
    return current_user
