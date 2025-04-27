import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Date, Boolean, Table, MetaData, inspect, text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import date

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models for ORM - Note we're not using these for direct operations,
# but they're useful for mapping results
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    function_location_id = Column(String, index=True)
    sap_function_location = Column(String)
    building_name = Column(String)
    building_number = Column(String)
    facility_type = Column(String)
    function = Column(String)
    macro_area = Column(String)
    micro_area = Column(String)
    proponent = Column(String)
    zone = Column(String)
    
    hvac_type = Column(ARRAY(String))  # PostgreSQL array type
    sprinkler = Column(String)
    fire_alarm = Column(String)
    power_source = Column(ARRAY(String))  # PostgreSQL array type
    vcp_status = Column(String)
    vcp_planned_date = Column(Date, nullable=True)
    smart_power_meter_status = Column(String)
    eifs = Column(String)
    eifs_installed_year = Column(Integer, nullable=True)
    
    exterior_cladding_condition = Column(String)
    interior_architectural_condition = Column(String)
    fire_protection_system_obsolete = Column(String)
    hvac_condition = Column(Integer, nullable=True)
    electrical_condition = Column(Integer, nullable=True)
    roofing_condition = Column(String)
    
    water_proofing_warranty = Column(String)
    water_proofing_warranty_date = Column(Date, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    full_inspection_completed = Column(String)

def create_tables():
    """Create all database tables if they don't exist"""
    # We use the SQL in reset_database.py instead
    pass

def drop_tables():
    """Drop all database tables - use with caution!"""
    conn = engine.connect()
    conn.execute(text("DROP TABLE IF EXISTS inspections"))
    conn.execute(text("DROP TABLE IF EXISTS users"))
    conn.commit()
    conn.close()

def get_db():
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(db, username: str):
    """Get a user by username"""
    return db.query(User).filter(User.username == username).first()

def create_user(db, username: str, password_hash: str):
    """Create a new user"""
    db_user = User(username=username, password_hash=password_hash)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_all_inspections(db):
    """Get all inspections"""
    return db.query(Inspection).all()

def get_inspection(db, inspection_id: int):
    """Get a single inspection by ID"""
    return db.query(Inspection).filter(Inspection.id == inspection_id).first()

def format_array_for_postgres(value):
    """Format a list as a PostgreSQL array string"""
    if not value:
        return "{}"
    if isinstance(value, str):
        # If it's already a string, wrap it as a single-element array
        return "{" + value + "}"
    elif isinstance(value, list):
        # Format list as PostgreSQL array string
        formatted_items = []
        for item in value:
            if isinstance(item, str):
                # Escape quotes and wrap in quotes
                formatted_items.append('"' + item.replace('"', '\\"') + '"')
            else:
                formatted_items.append(str(item))
        return "{" + ",".join(formatted_items) + "}"
    else:
        # For any other type, convert to string and wrap as single-element array
        return "{" + str(value) + "}"

def create_inspection(db, inspection_data):
    """Create a new inspection using direct SQL to handle array types properly"""
    try:
        # Handle array fields specially for PostgreSQL
        hvac_type = inspection_data.get('hvac_type', [])
        power_source = inspection_data.get('power_source', [])
        
        conn = engine.connect()
        
        # Build the query and parameters
        columns = []
        placeholders = []
        params = {}
        
        for key, value in inspection_data.items():
            # Skip array fields which we'll handle separately
            if key in ['hvac_type', 'power_source']:
                continue
            
            columns.append(key)
            placeholders.append(f":{key}")
            params[key] = value
        
        # Add array fields with special handling
        columns.append('hvac_type')
        placeholders.append('CAST(:hvac_type AS TEXT[])')
        params['hvac_type'] = format_array_for_postgres(hvac_type)
        
        columns.append('power_source')
        placeholders.append('CAST(:power_source AS TEXT[])')
        params['power_source'] = format_array_for_postgres(power_source)
        
        columns_str = ', '.join(columns)
        placeholders_str = ', '.join(placeholders)
        
        # Execute insert query
        query = f"INSERT INTO inspections ({columns_str}) VALUES ({placeholders_str}) RETURNING id"
        result = conn.execute(text(query), params)
        
        inspection_id = result.scalar()
        conn.commit()
        conn.close()
        
        # Get the newly created inspection
        return get_inspection(db, inspection_id)
    except Exception as e:
        print(f"Error in create_inspection: {e}")
        print(f"Data: {inspection_data}")
        print(f"HVAC Type: {hvac_type}")
        print(f"Power Source: {power_source}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

def update_inspection(db, inspection_id: int, inspection_data):
    """Update an existing inspection using direct SQL to handle array types properly"""
    try:
        # Handle array fields specially for PostgreSQL
        hvac_type = inspection_data.get('hvac_type', [])
        power_source = inspection_data.get('power_source', [])
        
        conn = engine.connect()
        
        # Build the query and parameters
        set_clauses = []
        params = {'id': inspection_id}
        
        for key, value in inspection_data.items():
            # Skip array fields which we'll handle separately
            if key in ['hvac_type', 'power_source']:
                continue
            
            set_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        # Add array fields with special handling
        set_clauses.append("hvac_type = CAST(:hvac_type AS TEXT[])")
        params['hvac_type'] = format_array_for_postgres(hvac_type)
        
        set_clauses.append("power_source = CAST(:power_source AS TEXT[])")
        params['power_source'] = format_array_for_postgres(power_source)
        
        set_str = ', '.join(set_clauses)
        
        # Execute update query
        query = f"UPDATE inspections SET {set_str} WHERE id = :id"
        conn.execute(text(query), params)
        
        conn.commit()
        conn.close()
        
        # Get the updated inspection
        return get_inspection(db, inspection_id)
    except Exception as e:
        print(f"Error in update_inspection: {e}")
        print(f"Data: {inspection_data}")
        print(f"HVAC Type: {hvac_type}")
        print(f"Power Source: {power_source}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

def delete_inspection(db, inspection_id: int):
    """Delete an inspection"""
    try:
        conn = engine.connect()
        conn.execute(text("DELETE FROM inspections WHERE id = :id"), {"id": inspection_id})
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error in delete_inspection: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

def migrate_from_sheets(inspections_data, users_data):
    """Migrate data from Google Sheets to Postgres"""
    db = SessionLocal()
    conn = engine.connect()
    
    try:
        # Migrate users
        for user in users_data:
            try:
                # Check if user already exists
                if 'username' not in user or not user['username']:
                    continue
                    
                # Check if user exists
                result = conn.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": user.get('username')}
                )
                
                if not result.fetchone():
                    # Insert user
                    conn.execute(
                        text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"),
                        {"username": user.get('username'), "password_hash": user.get('password_hash')}
                    )
                    conn.commit()
            except Exception as e:
                print(f"Error migrating user {user.get('username', 'unknown')}: {str(e)}")
                continue
        
        # Migrate inspections
        for inspection in inspections_data:
            try:
                # Convert numeric values from strings if necessary
                hvac_condition = None
                if 'hvac_condition' in inspection and inspection['hvac_condition']:
                    try:
                        hvac_condition = int(inspection['hvac_condition'])
                    except (ValueError, TypeError):
                        hvac_condition = None
                        
                electrical_condition = None
                if 'electrical_condition' in inspection and inspection['electrical_condition']:
                    try:
                        electrical_condition = int(inspection['electrical_condition'])
                    except (ValueError, TypeError):
                        electrical_condition = None
                        
                eifs_installed_year = None
                if 'eifs_installed_year' in inspection and inspection['eifs_installed_year']:
                    try:
                        eifs_installed_year = int(inspection['eifs_installed_year'])
                    except (ValueError, TypeError):
                        eifs_installed_year = None
                        
                latitude = None
                if 'latitude' in inspection and inspection['latitude']:
                    try:
                        latitude = float(inspection['latitude'])
                    except (ValueError, TypeError):
                        latitude = None
                        
                longitude = None
                if 'longitude' in inspection and inspection['longitude']:
                    try:
                        longitude = float(inspection['longitude'])
                    except (ValueError, TypeError):
                        longitude = None
                
                # Process hvac_type field as array
                hvac_type = inspection.get('hvac_type', '')
                if isinstance(hvac_type, str):
                    if hvac_type:
                        hvac_type = [item.strip() for item in hvac_type.split(',')]
                    else:
                        hvac_type = []
                elif not isinstance(hvac_type, list):
                    hvac_type = [str(hvac_type)] if hvac_type else []
                
                # Process power_source field as array
                power_source = inspection.get('power_source', '')
                if isinstance(power_source, str):
                    if power_source:
                        power_source = [item.strip() for item in power_source.split(',')]
                    else:
                        power_source = []
                elif not isinstance(power_source, list):
                    power_source = [str(power_source)] if power_source else []
                
                # Format arrays for PostgreSQL
                hvac_type_array = format_array_for_postgres(hvac_type)
                power_source_array = format_array_for_postgres(power_source)
                
                # Parse dates
                vcp_planned_date = None
                if 'vcp_planned_date' in inspection and inspection['vcp_planned_date']:
                    try:
                        vcp_planned_date = inspection['vcp_planned_date']
                    except (ValueError, TypeError):
                        vcp_planned_date = None
                        
                water_proofing_warranty_date = None
                if 'water_proofing_warranty_date' in inspection and inspection['water_proofing_warranty_date']:
                    try:
                        water_proofing_warranty_date = inspection['water_proofing_warranty_date']
                    except (ValueError, TypeError):
                        water_proofing_warranty_date = None
                
                # Insert inspection using direct SQL
                conn.execute(
                    text("""
                        INSERT INTO inspections (
                            function_location_id, sap_function_location, building_name, building_number,
                            facility_type, function, macro_area, micro_area, proponent, zone,
                            hvac_type, sprinkler, fire_alarm, power_source, vcp_status,
                            vcp_planned_date, smart_power_meter_status, eifs, eifs_installed_year,
                            exterior_cladding_condition, interior_architectural_condition,
                            fire_protection_system_obsolete, hvac_condition, electrical_condition,
                            roofing_condition, water_proofing_warranty, water_proofing_warranty_date,
                            latitude, longitude, full_inspection_completed
                        ) VALUES (
                            :function_location_id, :sap_function_location, :building_name, :building_number,
                            :facility_type, :function, :macro_area, :micro_area, :proponent, :zone,
                            CAST(:hvac_type AS TEXT[]), :sprinkler, :fire_alarm, CAST(:power_source AS TEXT[]), :vcp_status,
                            :vcp_planned_date, :smart_power_meter_status, :eifs, :eifs_installed_year,
                            :exterior_cladding_condition, :interior_architectural_condition,
                            :fire_protection_system_obsolete, :hvac_condition, :electrical_condition,
                            :roofing_condition, :water_proofing_warranty, :water_proofing_warranty_date,
                            :latitude, :longitude, :full_inspection_completed
                        )
                    """),
                    {
                        "function_location_id": inspection.get('function_location_id', ''),
                        "sap_function_location": inspection.get('sap_function_location', ''),
                        "building_name": inspection.get('building_name', ''),
                        "building_number": inspection.get('building_number', ''),
                        "facility_type": inspection.get('facility_type', ''),
                        "function": inspection.get('function', ''),
                        "macro_area": inspection.get('macro_area', ''),
                        "micro_area": inspection.get('micro_area', ''),
                        "proponent": inspection.get('proponent', ''),
                        "zone": inspection.get('zone', ''),
                        "hvac_type": hvac_type_array,
                        "sprinkler": inspection.get('sprinkler', ''),
                        "fire_alarm": inspection.get('fire_alarm', ''),
                        "power_source": power_source_array,
                        "vcp_status": inspection.get('vcp_status', ''),
                        "vcp_planned_date": vcp_planned_date,
                        "smart_power_meter_status": inspection.get('smart_power_meter_status', ''),
                        "eifs": inspection.get('eifs', ''),
                        "eifs_installed_year": eifs_installed_year,
                        "exterior_cladding_condition": inspection.get('exterior_cladding_condition', ''),
                        "interior_architectural_condition": inspection.get('interior_architectural_condition', ''),
                        "fire_protection_system_obsolete": inspection.get('fire_protection_system_obsolete', ''),
                        "hvac_condition": hvac_condition,
                        "electrical_condition": electrical_condition,
                        "roofing_condition": inspection.get('roofing_condition', ''),
                        "water_proofing_warranty": inspection.get('water_proofing_warranty', ''),
                        "water_proofing_warranty_date": water_proofing_warranty_date,
                        "latitude": latitude,
                        "longitude": longitude,
                        "full_inspection_completed": inspection.get('full_inspection_completed', '')
                    }
                )
                conn.commit()
            except Exception as e:
                print(f"Error migrating inspection: {str(e)}")
                print(f"Data: {inspection}")
                print(f"HVAC Type: {hvac_type}")
                print(f"Power Source: {power_source}")
                conn.rollback()
                # Continue with other records
                continue
    except Exception as e:
        print(f"Error in migrate_from_sheets: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
        db.close()
