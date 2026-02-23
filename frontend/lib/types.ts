export interface Tweet {
  tweet_id: string;
  text: string;
  created_at: string;
  author_id: string;
  like_count: number;
  retweet_count: number;
  reply_count: number;
  quote_count: number;
  impression_count: number;
  bookmark_count: number;
  total_engagement: number;
  name: string;
  username: string;
  profile_image_url: string;
  is_curated: number;
  user_bio?: string;
  verified?: number;
  followers_count?: number;
  relevance_score?: number;
  clinical_tags?: {
    tumor_types: string[];
    drugs: string[];
  };
}

export interface Abstract {
  abstract_number: string;
  title: string;
  body: string;
  presenter: string;
  session_type: string;
  session_title: string;
  poster_board_number: string;
  doi: string;
  url: string;
  subjects: string;
  genes: string;
  drugs: string;
  organizations: string;
  countries: string;
  tumor_type: string;
  session_rank: number;
  linked_tweet_count: number;
}

export interface Author {
  user_id: string;
  name: string;
  username: string;
  profile_image_url: string;
  is_curated: number;
  followers_count: number;
  tweet_count: number;
  total_engagement: number;
  avg_engagement: number;
}

export interface Stats {
  total_tweets: number;
  unique_authors: number;
  total_engagement: number;
  curated_active: number;
  total_abstracts: number;
}

export interface VolumeDay {
  date: string;
  tweets: number;
  authors: number;
  likes: number;
  retweets: number;
  replies: number;
  quotes: number;
  engagement: number;
}

export interface FilterOptions {
  tumors: string[];
  drugs: string[];
  session_types: string[];
}
