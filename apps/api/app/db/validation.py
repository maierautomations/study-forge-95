"""Database schema validation functions"""

import logging
from typing import Dict, Any, List, Tuple, Optional

from app.db.session import execute_query

logger = logging.getLogger(__name__)


async def validate_table_exists(table_name: str) -> Dict[str, Any]:
    """Check if a table exists in the public schema"""
    try:
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = $1
        )
        """
        result = await execute_query(query, table_name, fetch_one=True)
        exists = result['exists'] if result else False
        
        return {
            "table": table_name,
            "exists": exists,
            "status": "ok" if exists else "missing",
            "details": f"Table {table_name} {'exists' if exists else 'is missing'}"
        }
    except Exception as e:
        logger.error(f"Error checking table {table_name}: {e}")
        return {
            "table": table_name,
            "exists": False,
            "status": "error",
            "details": f"Error checking table: {str(e)}"
        }


async def validate_table_count(table_name: str) -> Dict[str, Any]:
    """Get row count for a table"""
    try:
        query = f"SELECT count(*) as count FROM {table_name}"
        result = await execute_query(query, fetch_one=True)
        count = result['count'] if result else 0
        
        return {
            "table": table_name,
            "count": count,
            "status": "ok",
            "details": f"Table {table_name} has {count} rows"
        }
    except Exception as e:
        logger.error(f"Error counting rows in {table_name}: {e}")
        return {
            "table": table_name,
            "count": None,
            "status": "error",
            "details": f"Error counting rows: {str(e)}"
        }


async def validate_index_exists(table_name: str, index_pattern: str) -> Dict[str, Any]:
    """Check if index exists for a table"""
    try:
        query = """
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename = $1 
        AND indexname LIKE $2
        """
        result = await execute_query(query, table_name, index_pattern, fetch_all=True)
        indexes = [row['indexname'] for row in result] if result else []
        
        return {
            "table": table_name,
            "pattern": index_pattern,
            "indexes": indexes,
            "exists": len(indexes) > 0,
            "status": "ok" if len(indexes) > 0 else "missing",
            "details": f"Found {len(indexes)} indexes matching '{index_pattern}': {', '.join(indexes) if indexes else 'none'}"
        }
    except Exception as e:
        logger.error(f"Error checking indexes for {table_name}: {e}")
        return {
            "table": table_name,
            "pattern": index_pattern,
            "indexes": [],
            "exists": False,
            "status": "error",
            "details": f"Error checking indexes: {str(e)}"
        }


async def validate_rls_enabled(table_name: str) -> Dict[str, Any]:
    """Check if RLS (Row Level Security) is enabled for a table"""
    try:
        query = """
        SELECT relname, relrowsecurity 
        FROM pg_class 
        WHERE relname = $1 
        AND relkind = 'r'
        """
        result = await execute_query(query, table_name, fetch_one=True)
        
        if not result:
            return {
                "table": table_name,
                "rls_enabled": False,
                "status": "error",
                "details": f"Table {table_name} not found"
            }
        
        rls_enabled = result['relrowsecurity'] if result else False
        
        return {
            "table": table_name,
            "rls_enabled": rls_enabled,
            "status": "ok" if rls_enabled else "disabled",
            "details": f"RLS is {'enabled' if rls_enabled else 'disabled'} for {table_name}"
        }
    except Exception as e:
        logger.error(f"Error checking RLS for {table_name}: {e}")
        return {
            "table": table_name,
            "rls_enabled": False,
            "status": "error",
            "details": f"Error checking RLS: {str(e)}"
        }


async def validate_rls_policies(table_name: str) -> Dict[str, Any]:
    """Check RLS policies for a table"""
    try:
        query = """
        SELECT policyname, permissive, roles, cmd, qual, with_check
        FROM pg_policies 
        WHERE tablename = $1
        ORDER BY policyname
        """
        result = await execute_query(query, table_name, fetch_all=True)
        policies = []
        
        if result:
            for row in result:
                policies.append({
                    "name": row['policyname'],
                    "permissive": row['permissive'],
                    "roles": row['roles'],
                    "command": row['cmd'],
                    "using": row['qual'],
                    "with_check": row['with_check']
                })
        
        return {
            "table": table_name,
            "policy_count": len(policies),
            "policies": policies,
            "status": "ok" if len(policies) > 0 else "no_policies",
            "details": f"Found {len(policies)} RLS policies for {table_name}"
        }
    except Exception as e:
        logger.error(f"Error checking RLS policies for {table_name}: {e}")
        return {
            "table": table_name,
            "policy_count": 0,
            "policies": [],
            "status": "error",
            "details": f"Error checking RLS policies: {str(e)}"
        }


async def validate_schema_complete() -> Dict[str, Any]:
    """Complete schema validation according to P1.1 requirements"""
    results = {}
    
    # Required tables from P1.1
    required_tables = ["chunks", "embeddings"]
    
    # 1. Check if tables exist
    for table in required_tables:
        results[f"{table}_exists"] = await validate_table_exists(table)
        
        # If table exists, check count (should be 0 for new tables)
        if results[f"{table}_exists"]["exists"]:
            results[f"{table}_count"] = await validate_table_count(table)
    
    # 2. Check required indexes
    if results.get("chunks_exists", {}).get("exists"):
        results["chunks_tsv_index"] = await validate_index_exists("chunks", "idx_chunks_tsv")
    
    if results.get("embeddings_exists", {}).get("exists"):
        results["embeddings_vector_index"] = await validate_index_exists("embeddings", "%ivfflat%")
    
    # 3. Check RLS is enabled
    for table in required_tables:
        if results.get(f"{table}_exists", {}).get("exists"):
            results[f"{table}_rls"] = await validate_rls_enabled(table)
            results[f"{table}_policies"] = await validate_rls_policies(table)
    
    # Overall status
    critical_checks = [
        "chunks_exists", "embeddings_exists", 
        "chunks_tsv_index", "embeddings_vector_index",
        "chunks_rls", "embeddings_rls"
    ]
    
    failed_checks = []
    for check in critical_checks:
        if check in results:
            status = results[check].get("status")
            if status not in ["ok", "no_policies"]:  # no_policies is acceptable for some checks
                failed_checks.append(check)
    
    overall_status = "pass" if not failed_checks else "fail"
    
    return {
        "overall_status": overall_status,
        "failed_checks": failed_checks,
        "detailed_results": results,
        "summary": {
            "tables_exist": all(
                results.get(f"{table}_exists", {}).get("exists", False) 
                for table in required_tables
            ),
            "indexes_exist": all(
                results.get(f"{table.replace('embeddings', 'embeddings_vector').replace('chunks', 'chunks_tsv')}_index", {}).get("exists", False)
                for table in required_tables
            ),
            "rls_enabled": all(
                results.get(f"{table}_rls", {}).get("rls_enabled", False)
                for table in required_tables
                if results.get(f"{table}_exists", {}).get("exists", False)
            )
        }
    }