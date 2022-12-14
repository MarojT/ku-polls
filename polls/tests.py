import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Question


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)

    def test_is_published(self):
        """Test that question is published"""
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertTrue(recent_question.is_published())

    def test_is_not_published(self):
        """Test that question is not published."""
        time = timezone.now() + datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertFalse(recent_question.is_published())

    def test_can_vote_published_question(self):
        """Test user can vote published question."""
        time = timezone.now() - datetime.timedelta(hours=24)
        end_time = timezone.now() + datetime.timedelta(hours=24)
        recent_question = Question(pub_date=time, end_date=end_time)
        self.assertTrue(recent_question.can_vote())

    def test_can_vote_not_published_question(self):
        """Test user can't vote question that not published."""
        time = timezone.now() + datetime.timedelta(hours=24)
        recent_question = Question(pub_date=time)
        self.assertFalse(recent_question.can_vote())

    def test_can_not_vote_end_question(self):
        """Test user can't vote end question."""
        time = timezone.now() + datetime.timedelta(hours=24)
        end_time = timezone.now() - datetime.timedelta(hours=24)
        question = Question(pub_date=time, end_date=end_time)
        self.assertFalse(question.can_vote())

    def test_can_vote_question(self):
        """Test user can vote question."""
        time = timezone.now() - datetime.timedelta(hours=24)
        end_time = timezone.now() + datetime.timedelta(hours=24)
        question = Question(pub_date=time, end_date=end_time)
        self.assertTrue(question.can_vote())

    def test_question_with_no_end_time(self):
        """Test user can vote question with no end time."""
        time = timezone.now() - datetime.timedelta(hours=24)
        question = Question(pub_date=time)
        self.assertTrue(question.can_vote())


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question],
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        question = create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question2, question1],
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        user = User.objects.create_user("user", "user@gmail.com", "12345")
        user.save()
        self.client.login(username="user", password="12345")
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class VoteModelTest(TestCase):
    def setup(self):
        user = User.objects.create_user("user", "user@gmail.com", "12345")
        user.save()

    def test_login_vote(self):
        self.client.login(username="user", password="12345")
        past_question = create_question(question_text='Past Question.',
                                        days=-1)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_not_login_vote(self):
        past_question = create_question(question_text='Past Question.', days=-1)
        url_question = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url_question)
        self.assertEqual(response.status_code, 302)
