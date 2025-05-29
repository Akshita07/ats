from rest_framework import viewsets, filters
from django.db.models import Q
from django.db.models import Case, When, Value, IntegerField
from .models import Candidate
from .serializers import CandidateSerializer


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def filter_queryset(self, queryset):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search', None)

        if search_query:
            # Split the search query into individual words
            search_terms = search_query.split()

            # Create a list to hold our Q objects
            q_objects = []

            # Create annotation for match quality
            when_conditions = []

            # Exact match should be first
            q_objects.append(Q(name__iexact=search_query))
            when_conditions.append(
                When(name__iexact=search_query, then=Value(1)))

            # All words in any order
            for term in search_terms:
                q_objects.append(Q(name__icontains=term))
                when_conditions.append(
                    When(name__icontains=term, then=Value(2)))

            # Combine all Q objects with OR
            combined_q = Q()
            for q in q_objects:
                combined_q |= q

            queryset = queryset.filter(combined_q).distinct()

            # Custom ordering based on match quality
            queryset = queryset.annotate(
                match_quality=Case(
                    *when_conditions,
                    default=Value(99),
                    output_field=IntegerField()
                )
            ).order_by('match_quality', 'name')

        return queryset
