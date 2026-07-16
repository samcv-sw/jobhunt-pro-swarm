# ──────────────────────────────────────────────────────────────────────────────
# pagination.py - Pagination & Sorting Utilities
# Helper functions for paginating query results and handling sorting
# ──────────────────────────────────────────────────────────────────────────────

import logging
from typing import Any, List, Dict, Optional, Tuple
from math import ceil

logger = logging.getLogger(__name__)


class PaginationHelper:
    """Helper for pagination operations."""
    
    @staticmethod
    def paginate(
        items: List[Any],
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Any], Dict[str, int]]:
        """Paginate a list of items."""
        # Validate parameters
        page = max(1, min(page, 1000))
        per_page = max(1, min(per_page, 100))
        
        total = len(items)
        total_pages = ceil(total / per_page)
        
        # Calculate offsets
        start = (page - 1) * per_page
        end = start + per_page
        
        # Get page items
        page_items = items[start:end]
        
        # Create pagination metadata
        metadata = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        }
        
        return page_items, metadata
    
    @staticmethod
    def get_offset_limit(page: int, per_page: int) -> Tuple[int, int]:
        """Convert page number to offset/limit for database queries."""
        page = max(1, page)
        per_page = max(1, min(per_page, 100))
        offset = (page - 1) * per_page
        return offset, per_page
    
    @staticmethod
    def build_pagination_link(
        base_url: str,
        page: int,
        per_page: int,
        params: Optional[Dict] = None,
    ) -> str:
        """Build pagination link."""
        from urllib.parse import urlencode
        
        query_params = {"page": page, "per_page": per_page}
        if params:
            query_params.update(params)
        
        return f"{base_url}?{urlencode(query_params)}"


class SortingHelper:
    """Helper for sorting operations."""
    
    SORT_ASC = "asc"
    SORT_DESC = "desc"
    
    @staticmethod
    def sort_items(
        items: List[Dict],
        sort_by: str,
        sort_order: str = "asc",
        allowed_fields: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Sort items by field."""
        # Validate field
        if allowed_fields and sort_by not in allowed_fields:
            logger.warning(f"Invalid sort field: {sort_by}")
            return items
        
        # Validate sort order
        reverse = sort_order.lower() == SortingHelper.SORT_DESC
        
        try:
            return sorted(items, key=lambda x: x.get(sort_by, ""), reverse=reverse)
        except Exception as e:
            logger.error(f"Failed to sort items: {e}")
            return items
    
    @staticmethod
    def build_sort_clause(sort_by: str, sort_order: str = "asc") -> str:
        """Build SQL sort clause."""
        reverse = sort_order.lower() == SortingHelper.SORT_DESC
        order = "DESC" if reverse else "ASC"
        return f"{sort_by} {order}"
    
    @staticmethod
    def validate_sort_params(
        sort_by: Optional[str],
        sort_order: Optional[str],
        allowed_fields: List[str],
    ) -> Tuple[Optional[str], str]:
        """Validate and normalize sort parameters."""
        if not sort_by or sort_by not in allowed_fields:
            return None, "asc"
        
        if sort_order not in ["asc", "desc"]:
            sort_order = "asc"
        
        return sort_by, sort_order


class FilterHelper:
    """Helper for filtering operations."""
    
    @staticmethod
    def build_filter_clause(
        filters: Dict[str, Any],
        allowed_fields: List[str],
    ) -> str:
        """Build SQL WHERE clause from filters."""
        clauses = []
        
        for field, value in filters.items():
            # Only allow specified fields (prevent SQL injection)
            if field not in allowed_fields:
                continue
            
            if value is None:
                clauses.append(f"{field} IS NULL")
            elif isinstance(value, str):
                # Escape single quotes
                escaped = value.replace("'", "''")
                clauses.append(f"{field} = '{escaped}'")
            elif isinstance(value, (int, float)):
                clauses.append(f"{field} = {value}")
            elif isinstance(value, bool):
                clauses.append(f"{field} = {1 if value else 0}")
            elif isinstance(value, (list, tuple)):
                values = ", ".join(
                    f"'{v}'" if isinstance(v, str) else str(v)
                    for v in value
                )
                clauses.append(f"{field} IN ({values})")
        
        return " AND ".join(clauses) if clauses else "1=1"
    
    @staticmethod
    def apply_filters(
        items: List[Dict],
        filters: Dict[str, Any],
    ) -> List[Dict]:
        """Filter items in-memory."""
        filtered = items
        
        for field, value in filters.items():
            if value is None:
                filtered = [x for x in filtered if x.get(field) is None]
            elif isinstance(value, (list, tuple)):
                filtered = [x for x in filtered if x.get(field) in value]
            else:
                filtered = [x for x in filtered if x.get(field) == value]
        
        return filtered


class SearchHelper:
    """Helper for full-text search."""
    
    @staticmethod
    def build_search_query(
        query: str,
        fields: List[str],
    ) -> str:
        """Build full-text search query."""
        # Simple keyword search across multiple fields
        keywords = query.lower().split()
        
        clauses = []
        for field in fields:
            for keyword in keywords:
                clauses.append(f"LOWER({field}) LIKE '%{keyword}%'")
        
        return " OR ".join(clauses) if clauses else "1=1"
    
    @staticmethod
    def search_items(
        items: List[Dict],
        query: str,
        fields: List[str],
    ) -> List[Dict]:
        """Search items in-memory."""
        if not query:
            return items
        
        keywords = query.lower().split()
        results = []
        
        for item in items:
            # Check if all keywords match any field
            matches = False
            for keyword in keywords:
                field_match = False
                for field in fields:
                    value = str(item.get(field, "")).lower()
                    if keyword in value:
                        field_match = True
                        break
                
                if field_match:
                    matches = True
                    break
            
            if matches:
                results.append(item)
        
        return results


class PaginationMetadata:
    """Consistent pagination metadata structure."""
    
    @staticmethod
    def create(
        total: int,
        page: int,
        per_page: int,
    ) -> Dict[str, Any]:
        """Create pagination metadata."""
        total_pages = ceil(total / per_page) if per_page > 0 else 1
        
        return {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "start_item": (page - 1) * per_page + 1 if total > 0 else 0,
            "end_item": min(page * per_page, total),
        }


# Usage example:
#
# from core.pagination import PaginationHelper, SortingHelper, FilterHelper, SearchHelper
#
# @app.get("/api/users")
# async def list_users(
#     page: int = 1,
#     per_page: int = 20,
#     sort_by: str = "created_at",
#     sort_order: str = "desc",
#     search: str = None,
# ):
#     # Get all users
#     users = db.get_all_users()
#     
#     # Apply search
#     if search:
#         users = SearchHelper.search_items(users, search, ["name", "email"])
#     
#     # Apply sorting
#     sort_by, sort_order = SortingHelper.validate_sort_params(
#         sort_by, sort_order, ["name", "email", "created_at"]
#     )
#     users = SortingHelper.sort_items(users, sort_by, sort_order)
#     
#     # Apply pagination
#     page_users, metadata = PaginationHelper.paginate(users, page, per_page)
#     
#     return paginated_response(
#         data=page_users,
#         total=len(users),
#         page=page,
#         per_page=per_page,
#     )
