import praw 
import json
from datetime import datetime


class reddit:
    def scrape(self,subreddit,posts_limit):
        with open("./Data/config.json") as f:
            config = json.load(f)


        reddit = praw.Reddit(
            client_id = config["client_id"],
            client_secret = config["SECRET_KEY"],
            user_agent = config["user_agent"],
        )

        # Target subreddit
        subreddit = reddit.subreddit(subreddit)

        # Prepare data for JSON
        posts_data = []
        
        # Extract image URL from the post
        def get_image_url(post):
            # Case 1: Direct image links (URL ends with an image extension)
            if post.url.endswith(('.jpg', '.png', '.gif')):
                return post.url
            
            # Case 2: Reddit-hosted media with a preview image
            if hasattr(post, "preview") and "images" in post.preview:
                return post.preview["images"][0]["source"]["url"]
            
            # Case 3: Gallery posts
            if hasattr(post, "gallery_data") and hasattr(post, "media_metadata"):
                image_urls = []
                for item in post.gallery_data["items"]:
                    media_id = item["media_id"]
                    if media_id in post.media_metadata:
                        media = post.media_metadata[media_id]
                        if "s" in media and "u" in media["s"]:
                            image_urls.append(media["s"]["u"])
                return image_urls  # Return a list of gallery image URLs
            
            # Case 4: No image found
            return None
        
        # Fetch the first 10 posts
        for post in subreddit.hot(limit=posts_limit):  
            # Check if the post URL is from Reddit
            if "reddit.com" not in post.url:
                # Convert the URL to the Reddit post permalink format
                post_url = f"https://www.reddit.com/r/worldnews/comments/{post.id}/"
            else:
                post_url = post.url
            print(post_url)
            # Get the image URL
            image_url = get_image_url(post)
                
            post_dict = {
                "post_id": post.id,
                "post_title": post.title,
                "post_body": post.selftext,
                "post_url":post_url,
                "image_url": image_url,
                "comments": []
            }
            # Fetch comments
            post.comments.replace_more(limit=None)  # Remove "load more comments"
            top_comments = post.comments[:50]  # Limit to top 50 comments
            for comment in top_comments:
                comment_dict = {
                    "comment_id": comment.id,
                    "comment_body": comment.body,
                    "replies": []
                }
                
                # Recursive function to fetch all replies
                def get_replies(comment, depth=1):
                    replies = []
                    for reply in comment.replies:
                        reply_dict = {
                            "reply_id": reply.id,
                            "reply_body": reply.body,
                            "depth": depth
                        }
                        # Fetch deeper replies recursively
                        reply_dict["replies"] = get_replies(reply, depth + 1)
                        replies.append(reply_dict)
                    return replies

                comment_dict["replies"] = get_replies(comment)
                post_dict["comments"].append(comment_dict)
            
            posts_data.append(post_dict)

        # Save to JSON file
        today = datetime.today().strftime("%Y-%m-%d")
        output_file = f"{str(subreddit)} {today}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, indent=4, ensure_ascii=False)

        # Function to count all comments and replies
        def count_comments(comments):
            total = 0
            for comment in comments:
                total += 1
                if "replies" in comment and isinstance(comment["replies"], list):
                    total += count_comments(comment["replies"])
            return total
        num_titles = len(posts_data)
        num_comments = sum(count_comments(post["comments"]) for post in posts_data)
        print(f"posts number: {str(num_titles)}")
        print(f"comments number: {str(num_comments)}")
        print(f"Data saved to {output_file}")
        
        
# Example usage
if __name__ == "__main__":
    # Create an instance of ExampleClass
    obj = reddit()
    # Call the methods
    obj.scrape(subreddit="investing", posts_limit=5)