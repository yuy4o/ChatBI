import unittest
import sys
import os

# Add the parent directory to sys.path to import the services module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.vector_db import search_metadata, init_vector_db, load_metadata_to_vector_db
from db import init_db

class TestVectorDB(unittest.TestCase):
    
    def test_search_metadata_limit(self):
        """Test if search results respect the limit parameter"""
        # Test with different limits
        limits = [10]
        for limit in limits:
            results = search_metadata('企业认证', limit=limit)
            self.assertLessEqual(len(results), limit)
    
    # def test_search_metadata_relevance(self):
    #     """Test if search results are relevant to the query"""
    #     # Test database level search
    #     db_results = search_metadata('超市')
    #     self.assertTrue(any('supermarket' in str(result).lower() for result in db_results))
    #
    #     # Test table level search
    #     table_results = search_metadata('用户')
    #     self.assertTrue(any('user' in str(result).lower() for result in table_results))
    #
    #     # Test column level search
    #     column_results = search_metadata('名称')
    #     self.assertTrue(any('name' in str(result).lower() for result in column_results))


if __name__ == '__main__':
    unittest.main()