
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.conf import settings
from bot.functions.jobs import (
    get_jobs_adzuna,
    get_jobs_careerjet,
    get_jobs_findwork,
    get_jobs_jooble,
    get_jobs_authentic,
    get_all_jobs
)

class JobSearchTests(TestCase):

    @patch('bot.functions.jobs.requests.get')
    def test_get_jobs_jobicy_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "jobs": [
                {
                    "id": 202,
                    "jobTitle": "Writer",
                    "companyName": "Media Co",
                    "jobGeo": "USA",
                    "pubDate": "2023-01-01",
                    "url": "http://jobicy.com/202",
                    "jobDescription": "Remote writer"
                }
            ]
        }
        mock_get.return_value = mock_response

        # Test with filters
        jobs = get_jobs_jobicy("writer", {"count": 10, "location": "USA", "industry": "media"})
        
        # Verify params
        args, kwargs = mock_get.call_args
        params = kwargs['params']
        self.assertEqual(params['count'], 10)
        self.assertEqual(params['geo'], "USA")
        self.assertEqual(params['industry'], "media")
        self.assertEqual(params['tag'], "writer")
        
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['job_title'], "Writer")
        self.assertEqual(jobs[0]['source'], "Jobicy")

    @patch('bot.functions.jobs.requests.get')
    def test_get_jobs_jobicy_default_geo(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"jobs": []}
        mock_get.return_value = mock_response

        # Test default "any" location behavior
        get_jobs_jobicy("writer", {"location": "Remote"})
        
        args, kwargs = mock_get.call_args
        params = kwargs['params']
        self.assertNotIn('geo', params) # Should be omitted for "Remote" -> default all regions


    @patch('bot.functions.jobs.requests.get')
    def test_get_jobs_adzuna_success(self, mock_get):
        # Mock settings
        with patch.object(settings, 'ADZUNA_APP_ID', 'test_id'), \
             patch.object(settings, 'ADZUNA_APP_KEY', 'test_key'):
            
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {
                "results": [
                    {
                        "id": "123",
                        "title": "Python Dev",
                        "company": {"display_name": "Tech Corp"},
                        "location": {"display_name": "London"},
                        "contract_type": "Permanent",
                        "created": "2023-01-01",
                        "description": "Code python",
                        "redirect_url": "http://example.com"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            jobs = get_jobs_adzuna("python")
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]['job_title'], "Python Dev")
            self.assertEqual(jobs[0]['source'], "Adzuna")

    @patch('bot.functions.jobs.requests.get')
    def test_get_jobs_careerjet_success(self, mock_get):
        # Mock settings
        with patch.object(settings, 'CAREERJET_API_KEY', 'test_key'), \
             patch.object(settings, 'CAREERJET_LOCALE', 'en_US'):
            
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {
                'jobs': [
                    {
                        "url": "http://careerjet.com/job1",
                        "title": "Java Dev",
                        "company": "Java Inc",
                        "locations": "London",
                        "date": "2023-01-01",
                        "description": "Code java"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            # Helper to match auth call
            def side_effect(*args, **kwargs):
                self.assertEqual(kwargs['auth'], ('test_key', ''))
                self.assertEqual(kwargs['params']['locale_code'], 'en_US')
                return mock_response
                
            mock_get.side_effect = side_effect
            
            jobs = get_jobs_careerjet("java")
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]['job_title'], "Java Dev")
            self.assertEqual(jobs[0]['source'], "Careerjet")

    @patch('bot.functions.jobs.requests.get')
    def test_get_jobs_findwork_success(self, mock_get):
        with patch.object(settings, 'FINDWORK_API_KEY', 'test_token'):
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {
                "results": [
                    {
                        "id": "fw1",
                        "role": "Frontend Dev",
                        "company_name": "Web Co",
                        "location": "NY",
                        "employment_type": ["full time"],
                        "date_posted": "2023-01-01",
                        "text": "React js",
                        "url": "http://findwork.dev/1",
                        "remote": True
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            jobs = get_jobs_findwork("frontend")
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]['job_title'], "Frontend Dev")
            self.assertEqual(jobs[0]['source'], "Findwork.dev")

    @patch('bot.functions.jobs.requests.post')
    def test_get_jobs_jooble_success(self, mock_post):
        with patch.object(settings, 'JOOBLE_API_KEY', 'test_key'):
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {
                "jobs": [
                    {
                        "id": "j1",
                        "title": "Backend Dev",
                        "company": "Back Co",
                        "location": "Berlin",
                        "type": "Full-time",
                        "updated": "2023-01-01",
                        "snippet": "Node js",
                        "link": "http://jooble.org/1"
                    }
                ]
            }
            mock_post.return_value = mock_response
            
            jobs = get_jobs_jooble("backend")
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]['job_title'], "Backend Dev")
            self.assertEqual(jobs[0]['source'], "Jooble")

    @patch('bot.functions.jobs.feedparser.parse')
    def test_get_jobs_authentic_success(self, mock_parse):
        # Mock feed entry
        entry = MagicMock()
        entry.title = "Designer"
        entry.description = "UI UX Designer needed"
        entry.link = "http://authentic.com/1"
        entry.id = "auth1"
        entry.published = "2023-01-01"
        
        mock_feed = MagicMock()
        mock_feed.entries = [entry]
        mock_parse.return_value = mock_feed
        
        # Test matching query
        jobs = get_jobs_authentic("designer")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['job_title'], "Designer")
        self.assertEqual(jobs[0]['source'], "Authentic Jobs")

    @patch('bot.functions.jobs.get_jobs')
    @patch('bot.functions.jobs.get_jobs_arbeitnow')
    @patch('bot.functions.jobs.get_jobs_remotive')
    @patch('bot.functions.jobs.get_jobs_jobicy')
    @patch('bot.functions.jobs.get_jobs_adzuna')
    @patch('bot.functions.jobs.get_jobs_careerjet')
    @patch('bot.functions.jobs.get_jobs_findwork')
    @patch('bot.functions.jobs.get_jobs_jooble')
    @patch('bot.functions.jobs.get_jobs_authentic')
    def test_get_all_jobs_aggregation(self, mock_authentic, mock_jooble, mock_findwork, 
                                     mock_careerjet, mock_adzuna, mock_jobicy, 
                                     mock_remotive, mock_arbeitnow, mock_jsearch):
        # Setup returns empty lists for simplicity, checking call count
        mock_jsearch.return_value = []
        mock_arbeitnow.return_value = []
        mock_remotive.return_value = []
        mock_jobicy.return_value = []
        mock_adzuna.return_value = []
        mock_careerjet.return_value = []
        mock_findwork.return_value = []
        mock_jooble.return_value = []
        mock_authentic.return_value = []
        
        get_all_jobs("test")
        
        self.assertTrue(mock_jsearch.called)
        self.assertTrue(mock_arbeitnow.called)
        self.assertTrue(mock_remotive.called)
        self.assertTrue(mock_jobicy.called)
        self.assertTrue(mock_adzuna.called)
        self.assertTrue(mock_careerjet.called)
        self.assertTrue(mock_findwork.called)
        self.assertTrue(mock_jooble.called)
        self.assertTrue(mock_authentic.called)
