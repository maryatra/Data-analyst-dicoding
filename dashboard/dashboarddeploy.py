import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import streamlit as st
import urllib


# Define DataAnalyzer class
class DataAnalyzer:
    def __init__(self, dataframe):
        self.df = dataframe

    def create_daily_orders_df(self):
        daily_orders = self.df.groupby(self.df['order_approved_at'].dt.date).agg({
            'order_id': 'count',
            'payment_value': 'sum'
        }).reset_index().rename(columns={'order_approved_at': 'date', 'order_id': 'order_count', 'payment_value': 'revenue'})
        return daily_orders

    def create_sum_spend_df(self):
        spend_df = self.df.groupby(self.df['order_approved_at'].dt.date).agg({
            'payment_value': 'sum'
        }).reset_index().rename(columns={'order_approved_at': 'date', 'payment_value': 'total_spend'})
        return spend_df

    def create_sum_order_items_df(self):
        items_df = self.df.groupby(['product_category_name_english']).agg({
            'order_id': 'count'
        }).reset_index().rename(columns={'order_id': 'product_count'})
        return items_df

    def review_score_df(self):
        review_score = self.df['review_score'].value_counts()
        common_score = self.df['review_score'].mode()[0]
        return review_score, common_score

    def create_bystate_df(self):
        state_df = self.df.groupby('customer_state').size().reset_index(name='customer_count')
        most_common_state = state_df.loc[state_df['customer_count'].idxmax()]['customer_state']
        return state_df, most_common_state

    def create_order_status(self):
        order_status_df = self.df['order_status'].value_counts()
        common_status = order_status_df.idxmax()
        return order_status_df, common_status
    def top_categories_by_orders(self):
        items_product = self.df[['order_id', 'product_id', 'price']].merge(
            self.df[['product_id', 'product_category_name_english']], on='product_id', how='inner')
        orders_ip = self.df[['order_id']].merge(items_product, on='order_id', how='inner')
        categories_by_orders = orders_ip['product_category_name_english'].value_counts().head(10)
        return categories_by_orders

    def top_categories_by_sales(self):
        items_product = self.df[['product_id', 'price', 'order_item_id']].merge(
            self.df[['product_id', 'product_category_name_english']], on='product_id', how='inner')
        items_product['total'] = items_product['price'] * items_product['order_item_id']
        categories_by_sales = items_product.groupby('product_category_name_english')['total'].sum().sort_values(ascending=False).head(10)
        return categories_by_sales



# Define BrazilMapPlotter class
class BrazilMapPlotter:
    def __init__(self, geo_df, plt, mpimg, urllib, st):
        self.geo_df = geo_df
        self.plt = plt
        self.mpimg = mpimg
        self.urllib = urllib
        self.st = st

    def plot(self):
        brazil_map_url = 'https://i.pinimg.com/originals/3a/0c/e1/3a0ce18b3c842748c255bc0aa445ad41.jpg'
        brazil_map = self.mpimg.imread(self.urllib.request.urlopen(brazil_map_url), 'jpg')
        fig, ax = self.plt.subplots(figsize=(10, 10))
        self.geo_df.plot(kind='scatter', x='geolocation_lng', y='geolocation_lat', alpha=0.3, s=0.3, color='maroon', ax=ax)
        ax.imshow(brazil_map, extent=[-73.98283055, -33.8, -33.75116944, 5.4])
        ax.axis('off')
        self.st.pyplot(fig)


# Configure Seaborn
sns.set(style='dark')

# Load the main dataset and geolocation dataset
csv_url = "https://raw.githubusercontent.com/maryatra/Data-analyst-dicoding/main/Data/df.csv"
all_df = pd.read_csv(csv_url)
print("CSV Columns:", all_df.columns.tolist())

# Display data preview
st.write("Data Preview Combined:")
st.write(all_df.head())  # Menampilkan lima baris pertama data

datetime_cols = [
    "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date",
    "order_purchase_timestamp", "shipping_limit_date"
]

# Check if all columns exist in the dataframe
datetime_cols = [col for col in datetime_cols if col in all_df.columns]
all_df[datetime_cols] = all_df[datetime_cols].apply(pd.to_datetime, errors='coerce')

# Sorting and resetting index
all_df.sort_values(by="order_approved_at", inplace=True)
all_df.reset_index(drop=True, inplace=True)

# Load the geolocation dataset
geo_df = pd.read_csv('https://raw.githubusercontent.com/maryatra/Data-analyst-dicoding/main/Data/geolocation.csv').drop_duplicates(subset='customer_unique_id')

# Display data preview
st.write("Data Preview Geo:")
st.write(geo_df.head())  # Menampilkan lima baris pertama data

# Sidebar configuration
with st.sidebar:
    st.image("https://raw.githubusercontent.com/maryatra/Data-analyst-dicoding/main/dashboard/pngwing.com (1).png", width=100)
    start_date, end_date = st.date_input("Select Date Range", [all_df["order_approved_at"].min(), all_df["order_approved_at"].max()])

# Filter data based on date range
filtered_df = all_df[(all_df["order_approved_at"] >= pd.to_datetime(start_date)) & (all_df["order_approved_at"] <= pd.to_datetime(end_date))]

# Initialize analysis and plotter classes
data_analyzer = DataAnalyzer(filtered_df)
map_plotter = BrazilMapPlotter(geo_df, plt, mpimg, urllib, st)

# Generate data for visualization
daily_orders = data_analyzer.create_daily_orders_df()
total_spend_data = data_analyzer.create_sum_spend_df()
order_items_data = data_analyzer.create_sum_order_items_df()
review_data, common_review = data_analyzer.review_score_df()
state_data, common_state = data_analyzer.create_bystate_df()
order_status_data, common_status = data_analyzer.create_order_status()
top_categories_orders = data_analyzer.top_categories_by_orders()
top_categories_sales = data_analyzer.top_categories_by_sales()

# Streamlit app layout
st.title("E-Commerce Public Data Analysis")
st.write("**This is a dashboard for analyzing E-Commerce public data.**")

# Daily Orders Visualization
st.subheader("Daily Orders Delivered")
st.markdown(f"Total Orders: **{daily_orders['order_count'].sum()}**")
st.markdown(f"Total Revenue: **{daily_orders['revenue'].sum()}**")

fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(data=daily_orders, x="date", y="order_count", marker="o", linewidth=2, color="#90CAF9")
ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", labelsize=15)
st.pyplot(fig)

# Customer Spending Visualization
st.subheader("Customer Spend Money")
st.markdown(f"Total Spend: **{total_spend_data['total_spend'].sum()}**")
st.markdown(f"Average Spend: **{total_spend_data['total_spend'].mean()}**")

fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(data=total_spend_data, x="date", y="total_spend", marker="o", linewidth=2, color="#90CAF9")
ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", labelsize=15)
st.pyplot(fig)

with st.expander("See Explanation"):
    st.write(
        "Most products in the top 50 saw an increased likelihood of sales during Black Friday (BF). Top-performing products on Black Friday are highly rated (usually best sellers).")

# Order Items Visualization
#New
# Top Categories by Orders Visualization
# Top Categories by Orders Visualization
st.subheader("Top 10 Most Ordered Product Categories")

try:
    fig, ax = plt.subplots(figsize=(20, 8))
    top_categories_orders.plot(kind='bar', ax=ax, color='#86bf91', zorder=2, width=0.85)
    ax.set_title('Top 10 Most Ordered Product Categories')
    ax.set_xlabel('Product Category')
    ax.set_ylabel('Number of Orders')
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, axis='y')
    st.pyplot(fig)
except ValueError as e:
    st.error(f"An error occurred while plotting Top Categories by Orders: {e}")

# Top Categories by Sales Visualization
st.subheader("Top 10 Product Categories by Sales Value")

try:
    fig, ax = plt.subplots(figsize=(20, 8))
    top_categories_sales.plot(kind='bar', ax=ax, color='#86bf91', zorder=2, width=0.85)
    ax.set_title('Top 10 Product Categories by Sales Value')
    ax.set_xlabel('Product Category')
    ax.set_ylabel('Total Sales Value')
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, axis='y')
    st.pyplot(fig)
except ValueError as e:
    st.error(f"An error occurred while plotting Top Categories by Sales Value: {e}")

with st.expander("See Explanation"):
    st.write("Based On chart the top sales occupied by product called cama_mesa_banho and the rest is visualized in chart above and the based on yhe values is just little bit different.")

st.subheader("Order Items")
st.markdown(f"Total Items: **{order_items_data['product_count'].sum()}**")
st.markdown(f"Average Items: **{order_items_data['product_count'].mean()}**")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(45, 25))

sns.barplot(x="product_count", y="product_category_name_english", data=order_items_data.head(5), palette="viridis", ax=ax[0], legend=False)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=80)
ax[0].set_title("Most sold products", loc="center", fontsize=90)
ax[0].tick_params(axis='y', labelsize=55)
ax[0].tick_params(axis='x', labelsize=50)

sns.barplot(x="product_count", y="product_category_name_english", data=order_items_data.sort_values(by="product_count", ascending=True).head(5), palette="viridis", ax=ax[1], legend=False)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=80)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Fewest products sold", loc="center", fontsize=90)
ax[1].tick_params(axis='y', labelsize=55)
ax[1].tick_params(axis='x', labelsize=50)

st.pyplot(fig)

# Review Scores Visualization
st.subheader("Review Score")
st.markdown(f"Average Review Score: **{review_data.mean():.2f}**")
st.markdown(f"Most Common Review Score: **{common_review}**")

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=review_data.index, y=review_data.values, palette="viridis", ax=ax, legend=False)
ax.set_title("Customer Review Scores for Service", fontsize=15)
ax.set_xlabel("Rating")
ax.set_ylabel("Count")
ax.tick_params(axis="x", labelsize=12)
ax.tick_params(axis="y", labelsize=12)

for index, value in enumerate(review_data.values):
    ax.text(index, value + 5, str(value), ha='center', va='bottom', fontsize= 12 )

st.pyplot(fig)
with st.expander("See Explanation"):
    st.write(
        "Based On chart the top sales occupied by product called cama_mesa_banho and the rest is visualized in chart above and the based on the values is just little bit different.")


# Customer Demographic Visualization
st.subheader("Customer Demographic")
tab1, tab2 = st.tabs(["State", "Geolocation"])

with tab1:
    st.markdown(f"Most Common State: **{common_state}**")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x=state_data.customer_state.value_counts().index, y=state_data.customer_count.values, palette="viridis", ax=ax)
    ax.set_title("Number of Customers from Each State", fontsize=15)
    ax.set_xlabel("State")
    ax.set_ylabel("Number of Customers")
    ax.tick_params(axis="x", labelsize=12)
    st.pyplot(fig)

with tab2:
    map_plotter.plot()
    with st.expander("See Explanation"):
        st.write("According to the graph that has been created, there are more customers in the southeast and south. Other information, there are more customers in cities that are capitals (São Paulo, Rio de Janeiro, Porto Alegre, and others).")

st.caption('Copyright (C) Muhammad Surya Putra 2024')
