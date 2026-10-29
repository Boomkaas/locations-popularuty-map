from rest_framework import serializers

from .models import Review, ReviewReaction

REACTION_VALUES = {
    "like": ReviewReaction.Value.LIKE,
    "dislike": ReviewReaction.Value.DISLIKE,
}
REACTION_NAMES = {
    ReviewReaction.Value.LIKE: "like",
    ReviewReaction.Value.DISLIKE: "dislike",
}


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")
    likes_count = serializers.IntegerField(read_only=True)
    dislikes_count = serializers.IntegerField(read_only=True)
    my_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "location",
            "author",
            "rating",
            "text",
            "likes_count",
            "dislikes_count",
            "my_reaction",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["location", "created_at", "updated_at"]

    def get_my_reaction(self, review) -> str | None:
        return REACTION_NAMES.get(review.my_reaction)


class ReactionSerializer(serializers.Serializer):
    value = serializers.ChoiceField(choices=list(REACTION_VALUES))
