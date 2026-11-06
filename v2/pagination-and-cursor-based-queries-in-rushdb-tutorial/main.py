#!/usr/bin/env python3
"""
Pagination and Cursor-Based Queries Tutorial for RushDB

This tutorial demonstrates:
1. Basic pagination with skip/limit
2. Cursor-based pagination using the "seek method"
3. Filtered pagination with category-specific queries
4. Building reusable pagination helpers
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from rushdb import RushDB, Record

# Load environment
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class PageResult:
    """Container for paginated query results."""
    items: list[Record]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


@dataclass
class CursorResult:
    """Container for cursor-based query results."""
    items: list[Record]
    next_cursor: Optional[str]
    has_more: bool


# =============================================================================
# Pagination Functions
# =============================================================================

def basic_pagination(page: int = 1, page_size: int = 10) -> PageResult:
    """
    Basic pagination using skip/limit.
    
    RushDB natively supports:
    - limit: Number of items per page
    - skip: Number of items to skip (offset)
    - total: Total count of matching records
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        PageResult with items and metadata
    """
    skip = (page - 1) * page_size
    
    result = db.records.find({
        "labels": ["ARTICLE"],
        "where": {"tutorial_seed": True},
        "limit": page_size,
        "skip": skip,
        "orderBy": {"slug": "asc"},
    })
    
    return PageResult(
        items=result.data,
        total=result.total,
        page=page,
        page_size=page_size,
        has_next=skip + page_size < result.total,
        has_prev=page > 1,
    )


def cursor_pagination(
    cursor: Optional[str] = None,
    page_size: int = 10,
    category: Optional[str] = None
) -> CursorResult:
    """
    Cursor-based pagination using the "seek method".
    
    This approach is more performant for large datasets because:
    - No expensive SKIP operation
    - Consistent query time regardless of page depth
    - Uses indexed ID field for efficient seeks
    
    Args:
        cursor: Last item's ID from previous page (None for first page)
        page_size: Number of items per page
        category: Optional category filter
        
    Returns:
        CursorResult with items and next cursor
    """
    where_clause = {"tutorial_seed": True}
    
    # Add category filter if specified
    if category:
        where_clause["category"] = category
    
    # Build query with cursor-based seek
    query = {
        "labels": ["ARTICLE"],
        "limit": page_size,
        "orderBy": {"slug": "asc"},
    }
    
    # If cursor provided, seek past it
    if cursor:
        where_clause["slug"] = {"$gt": cursor}
    
    query["where"] = where_clause
    
    result = db.records.find(query)
    
    # Determine next cursor
    next_cursor = None
    if result.data:
        # Last item's slug becomes the next cursor
        last_item = result.data[-1]
        next_cursor = last_item.id  # Use internal ID for stability
    
    return CursorResult(
        items=result.data,
        next_cursor=next_cursor,
        has_more=len(result.data) == page_size,
    )


def filtered_pagination(
    category: str,
    page: int = 1,
    page_size: int = 10
) -> PageResult:
    """
    Paginated query with category filtering.
    
    Demonstrates combining filters with pagination.
    """
    skip = (page - 1) * page_size
    
    result = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "category": category,
            "tutorial_seed": True,
        },
        "limit": page_size,
        "skip": skip,
        "orderBy": {"slug": "asc"},
    })
    
    return PageResult(
        items=result.data,
        total=result.total,
        page=page,
        page_size=page_size,
        has_next=skip + page_size < result.total,
        has_prev=page > 1,
    )


def paginated_iterator(page_size: int = 10, max_pages: Optional[int] = None):
    """
    Generator that yields all items across pages.
    
    Useful for processing large result sets without loading everything in memory.
    
    Args:
        page_size: Items per page
        max_pages: Optional limit on pages to fetch
        
    Yields:
        Individual Record objects
    """
    cursor = None
    pages_fetched = 0
    
    while True:
        if max_pages and pages_fetched >= max_pages:
            break
            
        result = cursor_pagination(cursor=cursor, page_size=page_size)
        
        for item in result.items:
            yield item
        
        if not result.has_more:
            break
            
        cursor = result.next_cursor
        pages_fetched += 1


# =============================================================================
# Demo Functions
# =============================================================================

def demo_basic_pagination():
    """Demonstrate basic skip/limit pagination."""
    print("\n=== Basic Pagination Demo (skip/limit) ===\n")
    
    # Fetch first page
    page1 = basic_pagination(page=1, page_size=10)
    print(f"Page 1: {len(page1.items)} items (total: {page1.total})")
    print(f"Has next: {page1.has_next}, Has prev: {page1.has_prev}")
    print("\nFirst 3 items:")
    for i, item in enumerate(page1.items[:3]):
        print(f"  {i+1}. {item.fields.get('title', 'N/A')} ({item.fields.get('category', 'N/A')})")
    
    # Fetch third page
    page3 = basic_pagination(page=3, page_size=10)
    print(f"\nPage 3: {len(page3.items)} items (total: {page3.total})")
    print(f"Has next: {page3.has_next}, Has prev: {page3.has_prev}")
    print("\nFirst 3 items:")
    for i, item in enumerate(page3.items[:3]):
        print(f"  {i+1}. {item.fields.get('title', 'N/A')} ({item.fields.get('category', 'N/A')})")


def demo_cursor_pagination():
    """Demonstrate cursor-based pagination."""
    print("\n=== Cursor-Based Pagination Demo ===\n")
    
    cursor = None
    
    # Fetch first 3 pages using cursor
    for page_num in range(1, 4):
        result = cursor_pagination(cursor=cursor, page_size=10)
        
        if not result.items:
            print("No more items")
            break
        
        # Show page summary
        first_slug = result.items[0].fields.get("slug", "N/A")
        last_slug = result.items[-1].fields.get("slug", "N/A")
        print(f"Page {page_num}: Items from '{first_slug}' to '{last_slug}'")
        print(f"  Items: {len(result.items)}, Has more: {result.has_more}")
        
        # Prepare cursor for next page
        cursor = result.next_cursor
        
        if not result.has_more:
            print("\nReached end of results")
            break


def demo_filtered_pagination():
    """Demonstrate pagination with category filtering."""
    print("\n=== Filtered Pagination Demo ===\n")
    
    categories = ["technology", "science", "business"]
    
    for category in categories:
        result = filtered_pagination(category=category, page=1, page_size=5)
        print(f"Category '{category}': {result.total} total articles")
        print("First 3:")
        for i, item in enumerate(result.items[:3]):
            print(f"  {i+1}. {item.fields.get('title', 'N/A')}")
        print()


def demo_paginated_iterator():
    """Demonstrate using paginated iterator for streaming results."""
    print("\n=== Paginated Iterator Demo ===\n")
    
    # Process items one by one (streaming style)
    processed = []
    for i, item in enumerate(paginated_iterator(page_size=10, max_pages=2)):
        processed.append(item.fields.get("title", "N/A"))
        if i < 5:  # Show first 5
            print(f"  Processing item {i+1}: {item.fields.get('slug')}")
    
    print(f"\nTotal items processed: {len(processed)}")


def demo_page_metadata():
    """Demonstrate comprehensive page metadata."""
    print("\n=== Page Metadata Demo ===\n")
    
    page_size = 10
    result = basic_pagination(page=2, page_size=page_size)
    
    total_pages = (result.total + page_size - 1) // page_size
    
    print(f"Page {result.page} of {total_pages}")
    print(f"Showing items {(result.page - 1) * page_size + 1} to {min(result.page * page_size, result.total)}")
    print(f"Total articles: {result.total}")
    print(f"Items per page: {result.page_size}")
    print(f"Navigation: Previous={'Yes' if result.has_prev else 'No'} | Next={'Yes' if result.has_next else 'No'}")


def check_data_exists() -> bool:
    """Verify that seed data exists."""
    result = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    return result.total > 0


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "="*60)
    print("  RushDB Pagination Tutorial")
    print("="*60)
    
    # Check for seed data
    if not check_data_exists():
        print("\nNo tutorial data found!")
        print("Please run 'python seed.py' first to populate the database.")
        sys.exit(1)
    
    # Run demos
    demo_basic_pagination()
    demo_cursor_pagination()
    demo_filtered_pagination()
    demo_paginated_iterator()
    demo_page_metadata()
    
    print("\n" + "="*60)
    print("  Tutorial Complete!")
    print("="*60)
    print("\nKey Takeaways:")
    print("  1. Use skip/limit for simple pagination with known total")
    print("  2. Use cursor pagination for large datasets and infinite scroll")
    print("  3. Combine filters with pagination for category views")
    print("  4. Use iterators to stream large results efficiently")
    print()


if __name__ == "__main__":
    main()
