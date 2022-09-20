from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Choice, Question, Vote


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]


class DetailView(LoginRequiredMixin, generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

    def get(self, request, pk):
        """
        Redirect web to different page by is_published and can_vote.
        """
        question = get_object_or_404(Question, pk=pk)
        user = request.user
        if not question.is_published():
            messages.error(request, "This poll didn't publish yet.")
            return HttpResponseRedirect(reverse('polls:index'))
        elif not question.can_vote():
            messages.error(request, "This poll has ended.")
            return HttpResponseRedirect(reverse('polls:index'))
        else:
            voted_choice = Vote.objects.filter(user=user)
            check = ""
            for select_choice in voted_choice:
                if select_choice.question == question:
                    check = select_choice.choice.choice_text
            return render(request, 'polls/detail.html', {'question': question, 'check': check, })


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'


def vote(request, question_id):
    """Add vote to choice of the current question."""
    user = request.user
    if not user.is_authenticated:
        return redirect('login')
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        voted_choice = Vote.objects.filter(user=user)
        for select in voted_choice:
            if select.question == question:
                select.choice = selected_choice
                select.save()
                return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
        new_vote = Vote.objects.create(user=user, choice=selected_choice)
        new_vote.save()
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
